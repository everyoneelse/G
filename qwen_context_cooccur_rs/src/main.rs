use std::collections::{BTreeSet, HashMap, HashSet};
use std::fs::File;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};

use anyhow::{Context, Result};
use clap::Parser;
use indicatif::{MultiProgress, ProgressBar, ProgressStyle};
use rayon::prelude::*;
use serde::Deserialize;
use tokenizers::{PaddingParams, Tokenizer};
use walkdir::WalkDir;

#[derive(Parser, Debug)]
#[command(name = "qwen_context_cooccur_rs", version, about = "Build token co-occurrence mapping using a HuggingFace tokenizer.json", long_about = None)]
struct Cli {
    /// Directory containing .jsonl files (one object per line, a 'text' field is expected)
    #[arg(long = "data-dir", value_name = "DIR", value_parser)]
    data_dir: PathBuf,

    /// Path to tokenizer.json (from a model repo) or directory containing it
    #[arg(long = "tokenizer", value_name = "PATH", default_value = "tokenizer.json")]
    tokenizer_path: PathBuf,

    /// Number of texts to tokenize per batch (higher == faster but more memory)
    #[arg(long = "batch-size", default_value_t = 512)]
    batch_size: usize,

    /// Fixed window size in tokens for co-occurrence statistics
    #[arg(long = "context-length", default_value_t = 128)]
    context_length: usize,

    /// Threads for parallel tokenization and accumulation
    #[arg(long = "num-threads", default_value_t = num_cpus::get())]
    num_threads: usize,

    /// Path to save the adjacency list TSV file
    #[arg(long = "out-file", value_name = "FILE", value_parser)]
    out_file: PathBuf,
}

#[derive(Deserialize)]
struct JsonLine {
    #[serde(default)]
    text: String,
}

fn accumulate_pairs(token_ids: &[u32], ctx_len: usize, adj: &mut HashMap<u32, HashSet<u32>>) {
    if token_ids.len() < 2 || ctx_len < 2 {
        return;
    }
    let mut start = 0;
    while start < token_ids.len() {
        let end = (start + ctx_len).min(token_ids.len());
        let segment = &token_ids[start..end];
        if segment.len() >= 2 {
            let mut uniq: HashSet<u32> = HashSet::with_capacity(segment.len());
            for &id in segment {
                uniq.insert(id);
            }
            for &token in &uniq {
                let entry = adj.entry(token).or_insert_with(HashSet::new);
                entry.extend(uniq.iter().copied());
            }
        }
        start += ctx_len;
    }
}

fn collect_jsonl_files(data_dir: &Path) -> Result<Vec<PathBuf>> {
    let mut files = Vec::new();
    for entry in WalkDir::new(data_dir) {
        let entry = entry?;
        if entry.file_type().is_file() {
            if let Some(ext) = entry.path().extension() {
                if ext == "jsonl" {
                    files.push(entry.into_path());
                }
            }
        }
    }
    files.sort();
    Ok(files)
}

fn load_tokenizer(path: &Path) -> Result<Tokenizer> {
    // If a directory is given, append tokenizer.json
    let tok_path = if path.is_dir() {
        path.join("tokenizer.json")
    } else {
        path.to_path_buf()
    };
    let tokenizer = Tokenizer::from_file(&tok_path)
        .map_err(|e| anyhow::anyhow!("Failed to load tokenizer from {:?}: {}", tok_path, e))?;

    // Ensure no special tokens are automatically added (match Python add_special_tokens=False)
    let mut tokenizer = tokenizer;
    tokenizer.with_padding(None::<PaddingParams>);

    Ok(tokenizer)
}

fn read_jsonl_texts(path: &Path) -> Result<Vec<String>> {
    let file = File::open(path).with_context(|| format!("Open file {:?}", path))?;
    let reader = BufReader::new(file);
    let mut texts = Vec::new();
    for line in reader.lines() {
        let line = line?;
        if line.is_empty() {
            continue;
        }
        if let Ok(obj) = serde_json::from_str::<JsonLine>(&line) {
            texts.push(obj.text);
        }
    }
    Ok(texts)
}

fn process_batch(tokenizer: &Tokenizer, texts: &[String], ctx_len: usize) -> Result<HashMap<u32, HashSet<u32>>> {
    let encodings = tokenizer
        .encode_batch(
            texts.iter().map(|t| t.as_str()).collect::<Vec<_>>(),
            false, // add_special_tokens = false
        )
        .map_err(|e| anyhow::anyhow!("Tokenization failed: {}", e))?;

    let mut local_adj: HashMap<u32, HashSet<u32>> = HashMap::new();
    for enc in encodings {
        let ids = enc.get_ids();
        if !ids.is_empty() {
            accumulate_pairs(ids, ctx_len, &mut local_adj);
        }
    }
    Ok(local_adj)
}

fn merge_adjacency(global: &mut HashMap<u32, HashSet<u32>>, local: HashMap<u32, HashSet<u32>>) {
    for (k, vset) in local.into_iter() {
        let entry = global.entry(k).or_insert_with(HashSet::new);
        entry.extend(vset);
    }
}

fn write_adjacency(out_file: &Path, adj: &HashMap<u32, HashSet<u32>>) -> Result<()> {
    let mut file = File::create(out_file).with_context(|| format!("Create {:?}", out_file))?;
    let mut keys: Vec<u32> = adj.keys().copied().collect();
    keys.sort_unstable();

    for token_id in keys {
        if let Some(neigh) = adj.get(&token_id) {
            let mut neighbours: BTreeSet<u32> = neigh.iter().copied().collect();
            neighbours.remove(&token_id); // remove self-loop
            let joined = neighbours
                .iter()
                .map(|n| n.to_string())
                .collect::<Vec<_>>()
                .join(" ");
            writeln!(file, "{}\t{}", token_id, joined)?;
        }
    }
    Ok(())
}

fn main() -> Result<()> {
    let args = Cli::parse();

    rayon::ThreadPoolBuilder::new()
        .num_threads(args.num_threads)
        .build_global()
        .ok();

    let jsonl_files = collect_jsonl_files(&args.data_dir)?;
    if jsonl_files.is_empty() {
        anyhow::bail!("No .jsonl files found under {:?}", args.data_dir);
    }

    println!(
        "Found {} jsonl files | Batch size: {} | Context len: {} | Threads: {}",
        jsonl_files.len(),
        args.batch_size,
        args.context_length,
        args.num_threads
    );

    // Load tokenizer once
    let tokenizer = load_tokenizer(&args.tokenizer_path)?;
    let tokenizer = Arc::new(tokenizer);

    // Shared adjacency map with mutex; use local maps per batch and merge
    let global_adj: Arc<Mutex<HashMap<u32, HashSet<u32>>>> = Arc::new(Mutex::new(HashMap::new()));

    // Progress bars
    let m = MultiProgress::new();
    let files_pb = m.add(ProgressBar::new(jsonl_files.len() as u64));
    files_pb.set_style(ProgressStyle::with_template("{spinner} Files {pos}/{len} [{elapsed_precise}] {wide_msg}").unwrap());

    // Iterate files in parallel (safe: tokenizer is Send+Sync)
    jsonl_files.par_iter().for_each(|path| {
        let _ = files_pb.inc(1);
        files_pb.set_message(path.file_name().unwrap_or_default().to_string_lossy().to_string());

        // Read all lines' texts first; then process in batches
        let texts = match read_jsonl_texts(path) {
            Ok(t) => t,
            Err(e) => {
                eprintln!("Failed to read {:?}: {}", path, e);
                return;
            }
        };
        if texts.is_empty() {
            return;
        }

        let mut start = 0usize;
        while start < texts.len() {
            let end = (start + args.batch_size).min(texts.len());
            let batch = &texts[start..end];
            start = end;

            let local = match process_batch(&tokenizer, batch, args.context_length) {
                Ok(m) => m,
                Err(e) => {
                    eprintln!("Tokenization failed for file {:?}: {}", path, e);
                    continue;
                }
            };

            if !local.is_empty() {
                if let Ok(mut guard) = global_adj.lock() {
                    merge_adjacency(&mut guard, local);
                }
            }
        }
    });

    // Write output
    let adj = Arc::try_unwrap(global_adj)
        .map_err(|_| anyhow::anyhow!("Arc unwrap failed; outstanding refs exist"))?
        .into_inner()
        .map_err(|_| anyhow::anyhow!("Mutex poisoned"))?;
    write_adjacency(&args.out_file, &adj)?;

    println!("Adjacency list saved to {}", args.out_file.canonicalize().unwrap_or(args.out_file.clone()).display());

    Ok(())
}
