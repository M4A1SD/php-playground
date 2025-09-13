<?php
session_start();
// php -S localhost:8000 student.php
// Function to load questions from JSON file
function loadQuestions() {
    $jsonData = file_get_contents('course_work.json');
    return json_decode($jsonData, true);
}

// Function to get a random question
function getRandomQuestion($questions) {
    if (empty($questions)) {
        return null;
    }
    $randomIndex = array_rand($questions);
    return $questions[$randomIndex];
}

// Load all questions
$allQuestions = loadQuestions();

// Check if we need a new question
if (!isset($_SESSION['current_question']) || isset($_POST['new_question'])) {
    $_SESSION['current_question'] = getRandomQuestion($allQuestions);
}

$currentQuestion = $_SESSION['current_question'];
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Course Work Question System</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
            padding-top: 20px;
            padding-bottom: 40px;
        }
        .question-card {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: 0.3s;
            border-radius: 10px;
            background-color: white;
            margin-bottom: 20px;
        }
        .question-text {
            white-space: pre-wrap;
            text-align: right;
            direction: rtl;
            font-size: 1.1rem;
            line-height: 1.6;
        }
        .question-prompt {
            font-weight: 600;
            margin-top: 15px;
            text-align: right;
            direction: rtl;
        }
        .btn-primary {
            background-color: #4e73df;
            border-color: #4e73df;
        }
        .btn-primary:hover {
            background-color: #2e59d9;
            border-color: #2e59d9;
        }
        .response-area {
            display: none;
            margin-top: 20px;
        }
        .header-section {
            background-color: #4e73df;
            color: white;
            padding: 15px;
            border-radius: 10px 10px 0 0;
            margin-bottom: 20px;
        }
        textarea {
            resize: vertical;
            min-height: 150px;
        }
        @media (max-width: 768px) {
            .container {
                padding: 0 15px;
            }
            .question-text, .question-prompt {
                font-size: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-10">
                <div class="question-card">
                    <div class="header-section text-center">
                        <h1 class="h3">Course Work Question System</h1>
                    </div>
                    
                    <div class="card-body">
                        <?php if ($currentQuestion): ?>
                            <!-- Text Content Section -->
                            <div class="mb-4">
                                <h5 class="card-title mb-3">Reading Material:</h5>
                                <div class="card">
                                    <div class="card-body question-text">
                                        <?php echo $currentQuestion['text']; ?>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Question Section -->
                            <div class="mb-4">
                                <h5 class="card-title mb-3">Question:</h5>
                                <div class="card">
                                    <div class="card-body">
                                        <p class="question-prompt"><?php echo $currentQuestion['questions']; ?></p>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Answer Form Section -->
                            <form id="answerForm" class="mb-4">
                                <div class="mb-3">
                                    <label for="answer" class="form-label">Your Answer:</label>
                                    <textarea class="form-control" id="answer" rows="6" placeholder="Type your answer here..."></textarea>
                                </div>
                                <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                                    <button type="submit" class="btn btn-primary">Submit Answer</button>
                                </div>
                            </form>
                            
                            <!-- Response Area -->
                            <div id="responseArea" class="response-area alert alert-info">
                                <h5>Feedback:</h5>
                                <div id="responseContent"></div>
                            </div>
                            
                            <!-- New Question Button -->
                            <div class="text-center mt-4">
                                <form method="post">
                                    <button type="submit" name="new_question" class="btn btn-secondary">Get New Question</button>
                                </form>
                            </div>
                            
                        <?php else: ?>
                            <div class="alert alert-warning">
                                No questions available. Please check the JSON file.
                            </div>
                        <?php endif; ?>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap & jQuery JS -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        $(document).ready(function() {
            // Handle form submission
            $("#answerForm").submit(function(e) {
                e.preventDefault();
                
                const answerText = $("#answer").val();
                const questionId = <?php echo isset($currentQuestion['id']) ? $currentQuestion['id'] : 'null'; ?>;
                
                if (!answerText.trim()) {
                    alert("Please enter your answer before submitting.");
                    return;
                }
                
                // Show loading state immediately
                $("#responseContent").html(`
                    <div class="d-flex align-items-center">
                        <div class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></div>
                        <span>Please wait, processing your answer...</span>
                    </div>
                `);
                $("#responseArea").removeClass("alert-danger").addClass("alert-info").show();
                
                // Send data to backend
                $.ajax({
                    url: "http://localhost:5000/process",
                    type: "POST",
                    contentType: "application/json",
                    data: JSON.stringify({
                        text: answerText,
                        question_id: questionId
                    }),
                    success: function(response) {
                        // Display response
                        $("#responseContent").html(response.feedback);
                        
                        // Check score and apply appropriate styling
                        if (response.total_score === 0) {
                            $("#responseContent").prepend("<div class='alert alert-danger'><strong>The answer is not fulfilling the requirements.</strong></div>");
                            $("#responseArea").removeClass("alert-success alert-info").addClass("alert-danger");
                        } else if (response.feedback && response.feedback.toLowerCase().includes("full answer")) {
                            $("#responseArea").removeClass("alert-danger alert-info").addClass("alert-success");
                        } else {
                            $("#responseArea").removeClass("alert-danger").addClass("alert-info");
                        }
                    },
                    error: function(xhr, status, error) {
                        $("#responseContent").html("Error: " + error);
                        $("#responseArea").removeClass("alert-info").addClass("alert-danger");
                    }
                });
            });
        });
    </script>
</body>
</html>
