import pandas as pd
import re
from typing import Dict, List, Tuple
import ahocorasick
from collections import defaultdict

class SynonymReplacer:
    def __init__(self, excel_file_path: str):

        self.excel_file_path = excel_file_path
        self.synonym_dict: Dict[str, str] = {}
        self.synonym_dict_label: Dict[str, str] = {}
        self.automaton = ahocorasick.Automaton()
        self.gps_name = ["GE", "西门子", "飞利浦", "Siemens", "通用电气", "Philips"]
        self.load_synonyms()
    
    def normalize_spaces(self, text: str) -> str:
        """
        处理文本中的空格：
        1. 中文与中文之间的空格去掉
        2. 英文与英文之间的多个空格替换为1个空格
        3. 中文与英文之间的空格保持不变
        """
        if not text:
            return text
            
        def is_chinese(char):
            """判断字符是否为中文"""
            return '\u4e00' <= char <= '\u9fff'
        
        def is_english(char):
            """判断字符是否为英文字母"""
            return char.isascii() and char.isalpha()
        
        result = []
        i = 0
        
        while i < len(text):
            char = text[i]
            
            if char == ' ':
                # 找到连续的空格
                space_start = i
                while i < len(text) and text[i] == ' ':
                    i += 1
                
                # 获取空格前后的字符
                prev_char = text[space_start - 1] if space_start > 0 else ''
                next_char = text[i] if i < len(text) else ''
                
                # 判断空格前后字符的类型
                prev_is_chinese = is_chinese(prev_char)
                prev_is_english = is_english(prev_char)
                next_is_chinese = is_chinese(next_char)
                next_is_english = is_english(next_char)
                
                # 根据规则处理空格
                if prev_is_chinese and next_is_chinese:
                    # 中文与中文之间的空格去掉
                    pass  # 不添加任何空格
                elif prev_is_english and next_is_english:
                    # 英文与英文之间的多个空格替换为1个空格
                    result.append(' ')
                else:
                    # 中文与英文之间的空格保持不变（保留1个空格）
                    result.append(' ')
            else:
                result.append(char)
                i += 1
        
        return ''.join(result)
    
    def load_synonyms(self):
        try:
            df = pd.read_json(self.excel_file_path, orient='records')
            standard_word_col = '名词'
            if standard_word_col not in df.columns:
                raise ValueError(f"Excel文件中未找到关键列: '{standard_word_col}'")
            
            for index, row in df.iterrows():
                standard_word = str(row[standard_word_col]).strip()
                
                if pd.isna(standard_word) or standard_word == '' or standard_word == 'nan':
                    continue
                
                if standard_word == "None" or standard_word.lower() == "none":
                    continue

                self._add_synonym_and_variants(standard_word.lower(), standard_word, '名词')

                skip_col_index = -1
                friend_company_index = -1
                for idx, col in enumerate(df.columns):
                    if "读音音标" in col:
                        skip_col_index = idx

                    if col == standard_word_col or "不作参考" in col or "文本 35" in col:
                        continue
                    
                    if "GE商品名1" in col:
                        friend_company_index = idx

                    if skip_col_index != -1 and idx >= skip_col_index and friend_company_index == -1:

                        continue

                    synonym = str(row[col]).strip()

                    if pd.isna(synonym) or synonym == '' or synonym == 'nan' or synonym == "/" or synonym == "None" or synonym == "none":
                        continue

                    if standard_word == "None":
                        continue

                    self._add_synonym_and_variants(synonym, standard_word, col)
                    

            for keyword, value in self.synonym_dict.items():


                self.automaton.add_word(keyword, (keyword, value))

            self.automaton.make_automaton()
            print(f"\n成功加载 {len(self.synonym_dict)} 个同义词映射并构建AC自动机。")
            
        except Exception as e:
            print(f"读取或处理Excel文件时出错: {e}")
            raise
    
    @classmethod
    def replace_question_marks(self, s):
        result = []
        wildcard_replacements = ['-', '_', '^', '', ' ', "—"] 

        def backtrack(current, index):
            if index == len(s):
                result.append(current)
                return
            if s[index] == '?':
                for repl in wildcard_replacements:
                    backtrack(current + repl, index + 1)
            else:
                backtrack(current + s[index], index + 1)
        
        backtrack("", 0)
        return result
    
    def _add_synonym_and_variants(self, synonym: str, standard_word: str, col: str):
        synonym = synonym.strip()
        if not synonym:
            return

        words_to_process = {synonym}
        wheather_expand = "?" in synonym
        if wheather_expand:
            expanded_words = set()
            replaced_question_marks = self.replace_question_marks(synonym)
            for repl in replaced_question_marks:
                expanded_words.add(repl)
            words_to_process = expanded_words
        

        final_variants = set()
        special_chars_pattern = r'[\-_`!@#$%^&=~—]'

        for word in words_to_process:
            final_variants.add(word)

            if wheather_expand and re.search(special_chars_pattern, word):
                variant_removed = re.sub(special_chars_pattern, '', word).strip()
                final_variants.add(variant_removed)

                variant_spaced = re.sub(special_chars_pattern, ' ', word).strip()
                variant_spaced = re.sub(r'\s+', ' ', variant_spaced)
                final_variants.add(variant_spaced)

        for variant in final_variants:
            if variant:
                self.synonym_dict[variant.lower()] = standard_word

                self.synonym_dict_label[variant.lower()] = col

    
    def replace_text(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        if not text.strip():
            return text,text, [],{"competitor_name_appear":None, 
                 "only_competitor_product_appear": None }

        # 在处理同义词替换之前先规范化空格
        text = self.normalize_spaces(text)

        split_pattern = r'((?:\n|\r|\t|\\[nrt])+)'
        parts = re.split(split_pattern, text)
        
        modified_parts = []
        all_replacements_made = []
        replaced_part_with_sws = []

        separator_pattern = r'((?:\n|\r|\t|\\[nrt])+)'
        found_competitor_name = False
        found_competitor_product = False
        for part in parts:
            if not part:  # Skip empty parts that can result from split
                continue
            # If the part is one of the delimiters, add it back as is.
            if re.fullmatch(separator_pattern, part):
                modified_parts.append(part)
                replaced_part_with_sws.append(part)
            else:
                # Process the text block for synonym replacement.
                replaced_part, replaced_part_with_sw, replacements, found_competitor_name_, found_competitor_product_ \
                      = self._replace_text_internal(part)
                modified_parts.append(replaced_part)
                all_replacements_made.extend(replacements)
                found_competitor_name = found_competitor_name or found_competitor_name_
                found_competitor_product = found_competitor_product or found_competitor_product_
                replaced_part_with_sws.append(replaced_part_with_sw)
        
        return "".join(modified_parts), "".join(replaced_part_with_sws), all_replacements_made, \
                {"competitor_name_appear":found_competitor_name, 
                 "only_competitor_product_appear": found_competitor_product }

    def _replace_text_internal(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:

        if not text:
            return text, text,  [], None, None

        lower_text = text.lower()
        all_matches = []

        def is_ascii_alphabet(char):
            return 'a' <= char <= 'z' or 'A' <= char <= 'Z'
        
        def is_chinese_char(char):
            return '\u4e00' <= char <= '\u9fff'
        
        def is_chinese_ascii_alphabet(char):
            return is_chinese_char(char) or is_ascii_alphabet(char)

        def is_ascii_num(char):
            return '0' <= char <= '9'
        

        def is_chinese_ascii_alphabet(char):
            return is_chinese_char(char) or is_ascii_alphabet(char)

        def is_ascii_num(char):
            return '0' <= char <= '9'
        
        def is_alphanumeric_english_only(s):
            """Return True if *s* consists solely of ASCII letters/digits or
            the connecting wildcard characters we允许视为"字母数字"的一部分。

            这样像 "3d-gre"、"abc_def" 这类带连字符/下划线/脱字符的整体被当成
            一个"单词"，以便在 valid_match 判定中能够正确识别其边界。"""

            if not s:
                return False

            allowed_extra = "-_"  # 可按需扩展
            for ch in s:
                if ch.isascii() and (ch.isalnum() or ch in allowed_extra):
                    continue
                return False
            return True

        for end_index, (found_keyword, standard_word) in self.automaton.iter(lower_text):
            start_index = end_index - len(found_keyword) + 1

            if start_index > 0 and lower_text[start_index - 1] == '_':
                continue
            if end_index + 1 < len(lower_text) and lower_text[end_index + 1] == '_':
                continue

            w_start, w_end = start_index, end_index
            while w_start > 0 and \
                is_alphanumeric_english_only(lower_text[w_start - 1]):
                w_start -= 1
            while w_end + 1 < len(lower_text) and is_alphanumeric_english_only(lower_text[w_end + 1]):
                w_end += 1
            
            containing_word = lower_text[w_start : w_end + 1]

            is_valid_match = False
            if is_alphanumeric_english_only(containing_word):
                if len(containing_word) == len(found_keyword):
                    is_valid_match = True
            else:
                is_valid_match = True

            if is_valid_match:
                is_chinese_alphabet_boundary_at_start_index = False
                is_chinese_alphabet_boundary_at_end_index = False
                if start_index > 1:
                    is_chinese_alphabet_boundary_at_start_index = \
                    (is_ascii_alphabet(text[start_index - 1]) == is_ascii_alphabet(standard_word[0])) and \
                        is_ascii_alphabet(text[start_index - 1])
                
                if end_index + 1 < len(text):
                    is_chinese_alphabet_boundary_at_end_index = \
                    (is_ascii_alphabet(text[end_index + 1]) == is_ascii_alphabet(standard_word[-1])) and \
                        is_ascii_alphabet(text[start_index - 1])

                original_slice = text[start_index : end_index + 1]

                sw_with_space = standard_word
                if is_chinese_alphabet_boundary_at_start_index:
                    sw_with_space = ' ' + sw_with_space
                
                if is_chinese_alphabet_boundary_at_end_index:
                    sw_with_space = sw_with_space + ' '

                all_matches.append((start_index, end_index, original_slice, standard_word, sw_with_space))


        if not all_matches:
            return text, text, [], None, None

        all_matches.sort(key=lambda x: (x[0], -x[1]))
        
        final_matches = []
        last_end = -1
        
        match_dict = defaultdict(list)
        found_competitor_name = False
        for match in all_matches:
            start, end, fs, sw, _ = match

            if sw in match_dict:
                existing_matchs = match_dict[sw]
                for existing_match in existing_matchs:

                    existing_start, existing_end, _, _, _ = existing_match
                    if existing_start < start and start < existing_end and \
                        end > existing_end:
                        inter_segment = text[existing_end + 1 : start]
                        char_before_overlap = text[start - 1] if start > 0 else ""
                        char_after_overlap = text[existing_end + 1] if existing_end + 1 < len(text) else ""

                        if not (char_before_overlap.isspace() or 
                                char_after_overlap.isspace() or 
                                re.search(r"\s", inter_segment)):
                            
                            updated_match = (
                                existing_start, 
                                end, 
                                text[existing_start : end + 1] , sw, match[4])
                            index_ = final_matches.index(existing_match)
                            final_matches[index_] = updated_match
                            last_end = end

                            label_ = self.synonym_dict_label[sw.lower()]
                            found_competitor_name = found_competitor_name or sw in self.gps_name and "名词" in label_

            if start > last_end:
                final_matches.append(match)
                match_dict[sw].append(match)
                last_end = end
                label_ = self.synonym_dict_label[sw.lower()]
                found_competitor_name = found_competitor_name or sw in self.gps_name and "名词" in label_
        
        result_parts = []
        result_parts_sw = []
        replacements_made = []
        founded_standard_words = [x[-2] for x in final_matches]
        last_index = 0

        found_competitor_product = False
        found_own_product = False
        for start, end, found_slice, standard, sw_with_space in final_matches:
            if found_slice.lower() in [x.lower() for x in self.gps_name]:
                continue
            label = self.synonym_dict_label[found_slice.lower()]
            found_competitor_product_ = any(x in label for x in self.gps_name)
            found_competitor_product = found_competitor_product or found_competitor_product_
            found_own_product_ = all(x not in label for x in self.gps_name)
            found_own_product = found_own_product or found_own_product_

        only_competitor_product_appear = found_competitor_product and (not found_own_product)

        for start, end, found_slice, standard, sw_with_space in final_matches:


            if founded_standard_words.count(standard) > 1 and found_slice.lower() != standard.lower():
                continue
            if found_slice == standard:
                continue
   
            if found_competitor_name and found_competitor_product_:
                continue

            result_parts.append(text[last_index:start])
            result_parts_sw.append(f"{text[last_index:start]}")
            result_parts_sw.append(f"{found_slice}")
            result_parts_sw.append(f"({standard})")
            result_parts.append(sw_with_space)
            replacements_made.append((found_slice, sw_with_space))
            last_index = end + 1
        
        result_parts.append(text[last_index:])
        result_parts_sw.append(text[last_index:])
        
        return "".join(result_parts), "".join(result_parts_sw), replacements_made, found_competitor_name, only_competitor_product_appear