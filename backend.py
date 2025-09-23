# server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from grader import RobustGrader
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load course work data
try:
    with open('course_work.json', 'r', encoding='utf-8') as f:
        course_data = json.load(f)
    print("✅ Course work data loaded successfully")
except Exception as e:
    print(f"❌ Failed to load course work data: {e}")
    course_data = []





@app.route("/process", methods=["POST"])
def process():
    """
    Process student answers using the RobustGrader
    Expected input: {"text": "student answer", "question_id": 1}
    """
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"response": "No text received", "status": "error"}), 400
        
        student_answer = data['text']
        question_id = data.get('question_id', 1)
        
        # Log the received data
        print(f"📝 Received student answer for question {question_id}")

        
        # Find the question data
        question_data = None
        for item in course_data:
            if item.get('id') == question_id:
                question_data = item
                break
        
        if not question_data:
            return jsonify({
                "response": f"Question ID {question_id} not found",
                "status": "error"
            }), 404
        
        # Extract rubric and answer key
        rubric = question_data.get('rubric', '')
        answer_key = question_data.get('answer', '')
        
        if not rubric or not answer_key:
            return jsonify({
                "response": "Missing rubric or answer key for this question",
                "status": "error"
            }), 500
        
        # Initialize grader with the student answer and answer key
        grader = RobustGrader(
            student_answer=student_answer,
            answer_key=answer_key
        )
        
      

        grading_result = grader.grade_answer(rubric, answer_key, student_answer)
        
        # Calculate final score
        total_score = sum(grading_result) if isinstance(grading_result, list) else 0
        max_possible = grader.max_points if hasattr(grader, 'max_points') else len(grading_result)
        
        # Generate feedback
        feedback = grader._feedback(grading_result)
        
        # Prepare response
        response_data = {
            "status": "success",
            "question_id": question_id,
            "score": total_score,
            "max_score": max_possible,
            "detailed_scores": grading_result,
            "feedback": feedback,
            "incorrect_parts": getattr(grader, 'incorrect_parts', [])
        }
        
        print(f"✅ Grading completed: {total_score}/{max_possible}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error during grading: {str(e)}")
        return jsonify({
            "response": f"Grading error: {str(e)}",
            "status": "error"
        }), 500

@app.route("/questions", methods=["GET"])
def get_questions():
    """
    Get all available questions
    """
    try:
        questions_info = []
        for item in course_data:
            questions_info.append({
                "id": item.get('id'),
                "question": item.get('questions', ''),
                "text_preview": item.get('text', '')[:200] + "..." if len(item.get('text', '')) > 200 else item.get('text', '')
            })
        
        return jsonify({
            "status": "success",
            "questions": questions_info,
            "total_questions": len(questions_info)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve questions: {str(e)}"
        }), 500

@app.route("/", methods=["GET"])
def health_check():
    """
    Simple health check endpoint
    """
    return jsonify({
        "status": "Flask server is running", 
        "message": "Ready to process requests",
        "endpoints": {
            "/": "Health check",
            "/questions": "Get available questions",
            "/process": "Grade student answers (POST)"
        }
    })

if __name__ == "__main__":
    print("Starting Flask server on http://localhost:5050")
    app.run(host='localhost', port=5050, debug=True)
