import requests
import json
import re
from sentence_transformers import SentenceTransformer, util
from typing import Dict, List, Optional, Tuple
import numpy as np


def fix_json_quotes(json_string):
    """
    General function to fix unescaped quotes in JSON string values.
    This works by finding JSON string patterns and escaping internal quotes.
    """
    # Pattern to match JSON string values: "key": "value with possible "quotes" inside"
    # This captures the key, colon, opening quote, content, and closing quote
    pattern = r'("[\w\d]+"\s*:\s*")([^"]*(?:"[^"]*"[^"]*)*?)("\s*[,}])'
    
    def escape_internal_quotes(match):
        prefix = match.group(1)  # "key": "
        content = match.group(2)  # the content that may have unescaped quotes
        suffix = match.group(3)   # " followed by , or }
        
        # Escape any quotes in the content
        escaped_content = content.replace('"', '\\"')
        
        return prefix + escaped_content + suffix
    
    # Apply the fix
    fixed_string = re.sub(pattern, escape_internal_quotes, json_string, flags=re.DOTALL)
    
    return fixed_string

def safe_json_loads(json_string):
    """
    Safely load JSON by attempting to fix common quote escaping issues.
    """
    try:
        # First try to load as-is
        return json.loads(json_string)
    except json.JSONDecodeError:
        # If it fails, try to fix quote issues
        try:
            fixed_string = fix_json_quotes(json_string)
            return json.loads(fixed_string)
        except json.JSONDecodeError as e:
            print(f"Could not parse JSON even after attempting fixes: {e}")
            print("Fixed string:")
            print(fixed_string)
            raise

class RobustGrader:
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model_name: str = "llama3:8b", student_answer: str = "", answer_key: str = ""):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.student_answer = student_answer
        self.answer_key = answer_key
        self.student_answer_parts = []
        self.incorrect_parts = []
        self.max_points = 0
        self.num_parts = 0

        # Load semantic similarity model (your existing setup)
        try:
            self.similarity_model = SentenceTransformer('MPA/sambert')
            
        except Exception as e:
            print(f"❌ Failed to load semantic model: {e}")
            self.similarity_model = None
        
        # Test Ollama connection
        self._test_ollama_connection()
    
    def _test_ollama_connection(self):
        """Test if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                
                return True
        except Exception as e:
            print(f"⚠️ Ollama connection issue: {e}")
            print("   Grader will work with semantic similarity only")
        return False
    
    def _call_ollama(self, prompt: str, max_retries: int = 2, num_predict: int = 100) -> Optional[str]:
        """Simple Ollama API call with error handling"""
        for attempt in range(max_retries):
            try:
                data = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistency
                        "top_p": 0.9,
                        "num_predict": num_predict   # Keep responses short
                    }
                }
                
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['response'].strip()
                    
            except Exception as e:
                print(f"   LLM attempt {attempt + 1} failed: {e}")
                
        print("   🔴 All LLM attempts failed, using fallback logic")
        return None
    
    def grade_answer(self, rubric: str, answer_key: str, student_answer: str) -> Dict:
        """
        Main grading function with simplified approach
        """
        print("\n🎯 Starting grading process...")
        
        # Step 1: Analyze rubric (simple extraction)
    
        rubric_info = self._analyze_rubric_simple(rubric)
      
        
        
   
        student_key_parts = self._split_answer_key(student_answer, rubric_info["num_parts"])
        # print(f"   📝 Studen Key parts: \n{student_key_parts}")

        # split answer key into parts
        answer_key_parts = self._split_answer_key(answer_key, rubric_info["num_parts"])
        # print(f"   📝 Answer key parts: \n{answer_key_parts}")




        # Step 3: Grade using semantic similarity + simple LLM checks
        print("⚖️ Step 3: Grading student answer...")
        grading_result = self._grade_with_semantic_focus(
            student_key_parts, student_answer, rubric_info, answer_key_parts
        )
        
      
        return grading_result
    
    def _analyze_rubric_simple(self, rubric: str) -> Dict[str, int]:
        """
        Step 1: Extract basic info from rubric 
        Uses simple prompts , and regex extraction
        """
        # Try LLM first with very simple prompt
        llm_result = self._call_ollama(f"""
        Read this rubric and answer two numbers only:

        {rubric}

        How many maximum points? How many parts to check?

        Format: "Points: X, Parts: Y"
        """)


        max_points = 3  # Safe default
        num_parts = 3   # Safe default
        
        if llm_result:
            # Try to extract numbers from LLM response
            points_match = re.search(r'points?:?\s*(\d+)', llm_result.lower())
            parts_match = re.search(r'parts?:?\s*(\d+)', llm_result.lower())
            
            if points_match:
                max_points = int(points_match.group(1))
                self.max_points = max_points
            if parts_match:
                num_parts = int(parts_match.group(1))
                self.num_parts = num_parts
        

        
        result = {
            "max_points": max_points,
            "num_parts": num_parts,
            "method": "llm" if llm_result else "fallback"
        }
        
        print(f"   📊 Detected: {max_points} points, {num_parts} parts ({result['method']})")
        return result

    def _split_answer_key(self, student_answer: str, num_parts: int) -> List[str]:
        """
        Step 2: Split answer key into parts
        Uses multiple strategies with fallbacks
        """

            # Ollama API endpoint
        # url = "http://localhost:11434/api/generate"

        prompt = f"""CRITICAL: Return ONLY the JSON array below, with NO additional text before or after. Do not add any explanations, headers, or other text.

            Analyze the Hebrew text and extract points based on these rules:
            THERE ARE {num_parts} parts total - this is the expected number of points to extract
            - If the text contains numbered ordinal markers (האחת, השנייה, השלישית, הרביעית, והאחרונה, etc.), extract each numbered point separately. according to {num_parts} parts total
            - If the text does NOT contain numbered markers, treat the entire text as ONE single point
            - IGNORE any introductory text, preamble, or general information that appears BEFORE the first numbered ordinal marker
            - Only start extracting from the first numbered marker (האחת, השנייה, etc.) onwards

            Return in this EXACT JSON format:
            [
            {{"point1": "COMPLETE FULL TEXT of the first point including all words"}},
            {{"point2": "COMPLETE FULL TEXT of the second point including all words"}},
            {{"point3": "COMPLETE FULL TEXT of the third point including all words"}}
            ... (increment point numbers: point1, point2, point3, etc. for each entry)
            ]

            IMPORTANT: 
            - Do NOT artificially split continuous text that lacks numbered markers
            - Include the COMPLETE text for each point. Do not truncate or shorten anything
            - CRITICAL: When numbered markers exist, IGNORE any text before the first marker and only extract from the numbered sections
            - Only create multiple JSON entries when there are clear numbered divisions in the text
            - Target {num_parts} total parts, but prioritize natural divisions over forced splitting
            - For numbered content: each point should include the ordinal marker and all text until the next marker (or end)

            Text to process:
            {student_answer}

            Remember: ONLY return the JSON array, nothing else."""

        data = {
            "model": self.model_name,
            "prompt":  prompt,
            "stream": False,  # Get complete response at once
            "options": {
                "num_predict": 10000,  # Allow longer responses
                "temperature": 0.1    # More deterministic output
            }
        }
        
        try:
            print("Sending request to Ollama...")
            response = requests.post(f"{self.ollama_url}/api/generate", json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result['response'][-1] != "]":
                    result['response'] += "]"
                return result['response']

            else:
                print(f"❌ Error: HTTP {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def _grade_with_semantic_focus(self, student_key_parts: List[str], student_answer: str, rubric_info: Dict, answer_key_parts: List[str]) -> Dict:
        """
        Main grading logic - semantic similarity focused with intelligent part matching
        
        First matches student parts with answer key parts, then performs targeted comparison.
        """

    
        final_scores = self._score_answers(answer_key_parts, student_key_parts, rubric_info["num_parts"])

  
        
        return final_scores
    
    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        try:
            embeddings = self.similarity_model.encode([text1, text2])
            similarity = float(util.cos_sim(embeddings[0], embeddings[1]))
            return similarity
        except Exception as e:
            print(f"      ⚠️ Semantic similarity failed: {e}")
            return 0.0
    
    def _simple_llm_check(self, reference: str, student_text: str) -> bool:
        # never used. I think it was LLM spam.
        """
        Very simple LLM check - just yes/no question
        """
        prompt = f"""
            Does the student answer contain this information?

            Required: {reference}

            Student: {student_text}

            Answer only: YES or NO
            """
        
        result = self._call_ollama(prompt)
        if result:
            result_clean = result.upper().strip()
            return "YES" in result_clean or "כן" in result_clean
        
        # Fallback: simple keyword matching
        return self._keyword_fallback(reference, student_text)
    
    def _score_answers(self, answer_key_parts: List[str], student_key_parts: List[str], num_parts: int) -> List[int]:
        """
        Score student answers against answer key using semantic similarity
        """
        if not answer_key_parts or not student_key_parts:
            print("⚠️ Warning: Missing answer key or student parts")
            return [0] * num_parts
            
        # AND. case of just one point.
        if len(answer_key_parts) == 1 and len(student_key_parts) == 1:
            semantic_mapping = self._semantic_score_answers(answer_key_parts, student_key_parts)
            if semantic_mapping[0][0] > 0.8:
                scores [0] = self.max_points
                return scores
         #     not sure what this was for. leaving it for now before the demo as it works rn.
        if len(answer_key_parts) == 1 or len(student_key_parts) == 1:
            print("⚠️ Warning: Only one part detected, returning zero scores")
            return [0] * len(student_key_parts)
        

     
        
        #  Semantic similarity matching
        if self.similarity_model:
            semantic_mapping = self._semantic_score_answers(answer_key_parts, student_key_parts)
            print(f"📊 Semantic mapping shape: {semantic_mapping.shape if hasattr(semantic_mapping, 'shape') else 'N/A'}")
        else:
            print("❌ No similarity model available")
            return [0] * num_parts


        # Ensure we have the right number of scores based on actual semantic mapping size
        actual_student_parts = len(semantic_mapping) if len(semantic_mapping) > 0 else num_parts
        scores = [0] * actual_student_parts
        
        for i in range(len(semantic_mapping)):
            # find the maximum value in the line i, call max value index j
            max_value_in_line = np.max(semantic_mapping[i])
            j = np.argmax(semantic_mapping[i])
            
            # then check the maximum value of the j column
            column_j = semantic_mapping[:, j]
            max_index_in_column_j = np.argmax(column_j)
            
            # if i==j and score > 0.7, give 1 point, otherwise 0 points
            if max_index_in_column_j == i and max_value_in_line > 0.7:
                scores[i] = 1
            else:
                # Only append if we have student answer parts and index is valid
                if hasattr(self, 'student_answer_parts') and i < len(self.student_answer_parts):
                    self.incorrect_parts.append(self.student_answer_parts[i])
                scores[i] = 0

        print(scores)
        return scores
    
    def _prepare_array(self, parts: List[str]) -> List[str]:
        """
        recieve LLM made "json" return just the values, raw answers.

        """

        data = safe_json_loads(parts)
        array = []
        for part_str in data:
            for key, value in part_str.items():
                array.append(value)
   
        return array
    
    def _semantic_score_answers(self, answer_key_parts: List[str], student_key_parts: List[str]) -> List[int]:
        """
        get dictionary of answers
        process to get just values
        turn to embeddings
        create similarity matrix
        """

        array1= self._prepare_array(student_key_parts)
        array2= self._prepare_array(answer_key_parts)

        self.student_answer_parts = array1
        # check for overlap and slice off the overlap


        model = SentenceTransformer('MPA/sambert')      
        embeddings1 = model.encode(array1)
        embeddings2 = model.encode(array2)
    
      # Calculate cross-similarity between JSON1 strings and JSON2 strings
        # Fix: swap order so rows=student, columns=answer_key
        similarities = util.cos_sim(embeddings1, embeddings2)
        print(similarities.numpy())

        return similarities.numpy()

    def _feedback(self, result: List[int], ):
        print(f"🔍 Incorrect Parts: {self.incorrect_parts}")
        if sum(result) == self.max_points:
            return "full answer"
        else:
            prompt = f"""
            this is the full answer {self.answer_key}
            this is the student answer {self.student_answer}
            this is the incorrect parts {self.incorrect_parts}
            your task is to give encouraging and helpful feedback on the student answer, based on the full answer and the incorrect parts. make it all about correcting the error. consice and profesional. IMPORTANT: Your response must be exactly 2 sentences maximum.
            """
        
        feedback_result = self._call_ollama(prompt, num_predict=1000)

        return feedback_result

      
  
"""
grader answer
    _analyze_rubric_simple
        call llm, and regex extract max points and num parts
    split answers to parts with _split_answer_key
        call llm, return json of sub parts of the full answer
    _grade_with_semantic_focus
        does nothing...
        _score_answers
            _semantic_score_answers
                _prepare_array
                    safe_json_loads
                        unload json that has unescaped quotes
                        fix_json_quotes
                            extracts values from json
                extracts raw data, into array.
                encode to embeddings
                create similarity matrix
            save incorrect answer partrs
            print scores
_feedback
    call llm and return feedback based on wrong answer parts
"""

"""
theres are 4 [ rubric 2 answer 1 feedback] LLM calls. price is ~ a cent per submition.\
2 embeddings calls

"""