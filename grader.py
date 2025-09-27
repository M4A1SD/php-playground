import requests
import json
import re
from sentence_transformers import SentenceTransformer, util
from typing import Dict, List, Optional
import numpy as np
from json_utils import safe_json_loads



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
    
    def _grade_answer(self, rubric: str, answer_key: str, student_answer: str) -> Dict:
            
        rubric_info = self._analyze_rubric_simple(rubric)
      
        
   
        student_key_parts = self._split_answer_key(student_answer, rubric_info["num_parts"])

        # split answer key into parts
        answer_key_parts = self._split_answer_key(answer_key, rubric_info["num_parts"])

        # extract raw data, into array.
        self.student_answer_parts= self._prepare_array(student_key_parts)
        self.answer_key_parts= self._prepare_array(answer_key_parts)



        
        final_scores = self._score_answers(rubric_info["num_parts"])

  
        
        return final_scores
      
    def _analyze_rubric_simple(self, rubric: str) -> Dict[str, int]:
        """
        Step 1: Extract basic info from rubric 
        Uses simple prompts , and regex extraction
        """
        llm_result = self._call_ollama(f"""
        Read this rubric and answer two numbers only:

        {rubric}

        How many maximum points? How many parts to check?

        Format: "Points: X, Parts: Y"
        """)

        
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
        # handle error
        if not max_points or not num_parts:
            print("❌ Error: Failed to extract max points or num parts")
            return {
                "max_points": 0,
                "num_parts": 0,
                "method": "fallback"
            }

        
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
       
    def _score_answers(self, num_parts: int) -> List[int]:
        """
        Score student answers against answer key using semantic similarity
        """
        if not self.answer_key_parts or not self.student_answer_parts:
            print("⚠️ Warning: Missing answer key or student parts")
            return [0] * num_parts
            
        # AND. case of just one point.
        if len(self.answer_key_parts) == 1 and len(self.student_answer_parts) == 1:
            semantic_mapping = self._semantic_score_answers()
            if semantic_mapping[0][0] > 0.8:
                scores [0] = self.max_points
                return scores
    
        

     
        
        #  Semantic similarity matching
        if self.similarity_model:
            semantic_mapping = self._semantic_score_answers()
            print(f"Semantic mapping shape: {semantic_mapping.shape if hasattr(semantic_mapping, 'shape') else 'N/A'}")
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
    
    def _semantic_score_answers(self) -> List[int]:
        """
        get dictionary of answers
        process to get just values
        turn to embeddings
        create similarity matrix
        """

        
        # check for overlap and slice off the overlap


        model = SentenceTransformer('MPA/sambert')      
        embeddings1 = model.encode(self.student_answer_parts)
        embeddings2 = model.encode(self.answer_key_parts)
    
      # Calculate cross-similarity between JSON1 strings and JSON2 strings
        # Fix: swap order so rows=student, columns=answer_key
        similarities = util.cos_sim(embeddings1, embeddings2)
        print(similarities.numpy())

        return similarities.numpy()

    def _feedback(self, result: List[int]):
        print(f"Incorrect Parts: {self.incorrect_parts}")
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
    _prepare_array
        safe_json_loads
            unload json that has unescaped quotes
            fix_json_quotes
            extracts values from json
        extracts raw data, into array.
    _score_answers
        _semantic_score_answers
            encode to embeddings
            create similarity matrix
            return similarity matrix
        save incorrect answer partrs            
        return scores
_feedback
    call llm and return feedback based on wrong answer parts
"""



"""
theres are 4 [ 1 rubric 2 answer 1 feedback] LLM calls. 
2 embeddings calls

"""