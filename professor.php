<?php
session_start();
// php -S localhost:8000 professor.php

// Function to load questions from JSON file
function loadQuestions() {
    $jsonFile = 'course_work.json';
    if (file_exists($jsonFile)) {
        $jsonData = file_get_contents($jsonFile);
        return json_decode($jsonData, true);
    }
    return [];
}

// Function to save questions to JSON file
function saveQuestions($questions) {
    $jsonData = json_encode($questions, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    file_put_contents('course_work.json', $jsonData);
}

// Function to get the next ID
function getNextId($questions) {
    $maxId = 0;
    foreach ($questions as $question) {
        if (isset($question['id']) && $question['id'] > $maxId) {
            $maxId = $question['id'];
        }
    }
    return $maxId + 1;
}

// Load all questions
$allQuestions = loadQuestions();

// Process form submission
$message = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_POST['add_question'])) {
        $text = $_POST['text'] ?? '';
        $questions = $_POST['questions'] ?? '';
        $answer = $_POST['answer'] ?? '';
        $rubric = $_POST['rubric'] ?? '';
        
        if (!empty($text) && !empty($questions)) {
            $newId = getNextId($allQuestions);
            $newQuestion = [
                'id' => $newId,
                'text' => $text,
                'questions' => $questions,
                'answer' => $answer,
                'rubric' => $rubric
            ];
            
            $allQuestions[] = $newQuestion;
            saveQuestions($allQuestions);
            $message = "Question #$newId added successfully!";
        } else {
            $message = "Error: Text and Question fields are required.";
        }
    }
    
    // Reload questions after changes
    $allQuestions = loadQuestions();
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Professor Question Management System</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
            padding-top: 20px;
            padding-bottom: 40px;
        }
        .card {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: 0.3s;
            border-radius: 10px;
            background-color: white;
            margin-bottom: 20px;
        }
        .header-section {
            background-color: #4e73df;
            color: white;
            padding: 15px;
            border-radius: 10px 10px 0 0;
            margin-bottom: 20px;
        }
        .btn-primary {
            background-color: #4e73df;
            border-color: #4e73df;
        }
        .btn-primary:hover {
            background-color: #2e59d9;
            border-color: #2e59d9;
        }
        textarea {
            resize: vertical;
            min-height: 150px;
            direction: rtl;
            text-align: right;
        }
        .rtl-text {
            direction: rtl;
            text-align: right;
        }
        .question-list {
            max-height: 600px;
            overflow-y: auto;
        }
        .question-item {
            border-left: 4px solid #4e73df;
        }
        .nav-tabs .nav-link.active {
            background-color: #4e73df;
            color: white;
            border-color: #4e73df;
        }
        .nav-tabs .nav-link {
            color: #4e73df;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-10">
                <div class="card">
                    <div class="header-section text-center">
                        <h1 class="h3">Professor Question Management System</h1>
                    </div>
                    
                    <div class="card-body">
                        <?php if (!empty($message)): ?>
                            <div class="alert <?php echo strpos($message, 'Error') === 0 ? 'alert-danger' : 'alert-success'; ?> alert-dismissible fade show">
                                <?php echo $message; ?>
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                            </div>
                        <?php endif; ?>
                        
                        <ul class="nav nav-tabs mb-4" id="myTab" role="tablist">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="add-tab" data-bs-toggle="tab" data-bs-target="#add-content" type="button" role="tab" aria-controls="add-content" aria-selected="true">Add New Question</button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="view-tab" data-bs-toggle="tab" data-bs-target="#view-content" type="button" role="tab" aria-controls="view-content" aria-selected="false">View Questions</button>
                            </li>
                        </ul>
                        
                        <div class="tab-content" id="myTabContent">
                            <!-- Add New Question Tab -->
                            <div class="tab-pane fade show active" id="add-content" role="tabpanel" aria-labelledby="add-tab">
                                <form method="post" action="">
                                    <div class="mb-3">
                                        <label for="text" class="form-label">Reading Material (Text):</label>
                                        <textarea class="form-control rtl-text" id="text" name="text" rows="8" required></textarea>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label for="questions" class="form-label">Question:</label>
                                        <textarea class="form-control rtl-text" id="questions" name="questions" rows="3" required></textarea>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label for="answer" class="form-label">Model Answer:</label>
                                        <textarea class="form-control rtl-text" id="answer" name="answer" rows="6"></textarea>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label for="rubric" class="form-label">Grading Rubric:</label>
                                        <textarea class="form-control rtl-text" id="rubric" name="rubric" rows="4"></textarea>
                                    </div>
                                    
                                    <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                                        <button type="submit" name="add_question" class="btn btn-primary">Add Question</button>
                                    </div>
                                </form>
                            </div>
                            
                            <!-- View Questions Tab -->
                            <div class="tab-pane fade" id="view-content" role="tabpanel" aria-labelledby="view-tab">
                                <div class="question-list">
                                    <?php if (empty($allQuestions)): ?>
                                        <div class="alert alert-info">
                                            No questions available. Add your first question!
                                        </div>
                                    <?php else: ?>
                                        <div class="accordion" id="questionAccordion">
                                            <?php foreach ($allQuestions as $index => $question): ?>
                                                <div class="accordion-item question-item mb-3">
                                                    <h2 class="accordion-header" id="heading<?php echo $question['id']; ?>">
                                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse<?php echo $question['id']; ?>" aria-expanded="false" aria-controls="collapse<?php echo $question['id']; ?>">
                                                            <strong>Question #<?php echo $question['id']; ?></strong>
                                                        </button>
                                                    </h2>
                                                    <div id="collapse<?php echo $question['id']; ?>" class="accordion-collapse collapse" aria-labelledby="heading<?php echo $question['id']; ?>" data-bs-parent="#questionAccordion">
                                                        <div class="accordion-body">
                                                            <div class="mb-3">
                                                                <h6>Reading Material:</h6>
                                                                <div class="card">
                                                                    <div class="card-body rtl-text">
                                                                        <?php echo nl2br(htmlspecialchars($question['text'])); ?>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                            
                                                            <div class="mb-3">
                                                                <h6>Question:</h6>
                                                                <div class="card">
                                                                    <div class="card-body rtl-text">
                                                                        <?php echo nl2br(htmlspecialchars($question['questions'])); ?>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                            
                                                            <?php if (!empty($question['answer'])): ?>
                                                                <div class="mb-3">
                                                                    <h6>Model Answer:</h6>
                                                                    <div class="card">
                                                                        <div class="card-body rtl-text">
                                                                            <?php echo nl2br(htmlspecialchars($question['answer'])); ?>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            <?php endif; ?>
                                                            
                                                            <?php if (!empty($question['rubric'])): ?>
                                                                <div class="mb-3">
                                                                    <h6>Grading Rubric:</h6>
                                                                    <div class="card">
                                                                        <div class="card-body rtl-text">
                                                                            <?php echo nl2br(htmlspecialchars($question['rubric'])); ?>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            <?php endif; ?>
                                                            
                                                        </div>
                                                    </div>
                                                </div>
                                            <?php endforeach; ?>
                                        </div>
                                    <?php endif; ?>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap & jQuery JS -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
