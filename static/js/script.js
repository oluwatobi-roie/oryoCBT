let currentIndex = 0;
let questions = [];
let answers = JSON.parse(localStorage.getItem('answers')) || {};
let isSubmitted = false;  // Flag to track if the test has been submitted
let totalTime = 1000 * 60; // 10 minutes in seconds
let timerInterval;
let endTime;

// Function to start the timer
function startTimer() {
    if (!localStorage.getItem('endTime')) {
        endTime = Date.now() + totalTime * 1000;  // Set end time in milliseconds
        localStorage.setItem('endTime', endTime);  // Save to localStorage
    } else {
        endTime = parseInt(localStorage.getItem('endTime'), 10);  // Retrieve end time
    }

    updateTimerDisplay();

    timerInterval = setInterval(() => {
        const currentTime = Date.now();
        const remainingTime = Math.max(0, Math.floor((endTime - currentTime) / 1000));  // Calculate remaining time

        if (remainingTime <= 0) {
            clearInterval(timerInterval);
            if (!isSubmitted) {
                alert('Time is up! Your answers will be submitted automatically.');
                document.getElementById('submit-button').style.display = 'block';
                prepareAnswers();  // Auto-submit when timer ends
                document.getElementById('test-form').submit();  // Submit the form
            }
        } else {
            totalTime = remainingTime;
            updateTimerDisplay();
        }
    }, 1000);
}

// Function to format and display the remaining time
function updateTimerDisplay() {
    const minutes = Math.floor(totalTime / 60);
    const seconds = totalTime % 60;
    document.getElementById('time-left').innerText =
        `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// Clear localStorage on submission to prevent reuse
function clearTimer() {
    localStorage.removeItem('endTime');
}



// Function to render the progress bar
function renderProgressBar() {
    const progressBar = document.getElementById('progress-bar');
    progressBar.innerHTML = '';
    questions.forEach((question, index) => {
        const button = document.createElement('button');
        button.className = answers[question.id] ? 'answered' : 'unanswered';
        button.innerText = index + 1;
        button.onclick = () => goToQuestion(index);
        progressBar.appendChild(button);
    });
}

// Function to render a question
function renderQuestion(index) {
    const question = questions[index];
    const selectedOption = answers[question.id] || null;

    // If the test is submitted, disable the input fields
    const disableInputs = isSubmitted ? 'disabled' : '';

    document.getElementById('question-container').innerHTML = `
        <h3>Question ${index + 1}: ${question.text}</h3>
        <div>
            <input type="radio" name="option" value="A" ${selectedOption === 'A' ? 'checked' : ''} ${disableInputs} onchange="selectAnswer(${question.id}, 'A')"> ${question.option_a}<br>
            <input type="radio" name="option" value="B" ${selectedOption === 'B' ? 'checked' : ''} ${disableInputs} onchange="selectAnswer(${question.id}, 'B')"> ${question.option_b}<br>
            <input type="radio" name="option" value="C" ${selectedOption === 'C' ? 'checked' : ''} ${disableInputs} onchange="selectAnswer(${question.id}, 'C')"> ${question.option_c}<br>
            <input type="radio" name="option" value="D" ${selectedOption === 'D' ? 'checked' : ''} ${disableInputs} onchange="selectAnswer(${question.id}, 'D')"> ${question.option_d}<br>
        </div>
    `;
}

// Function to handle navigation between questions
function navigate(step) {
    currentIndex += step;
    if (currentIndex < 0) currentIndex = 0;
    if (currentIndex >= questions.length) currentIndex = questions.length - 1;
    renderQuestion(currentIndex);
}

// Function to handle question navigation
function goToQuestion(index) {
    currentIndex = index;
    renderQuestion(index);
}

// Function to handle answer selection
function selectAnswer(questionId, option) {
    answers[questionId] = option;
    localStorage.setItem('answers', JSON.stringify(answers));  // Save answers to local storage
    renderProgressBar();
    checkIfAllAnswered();
}

// Function to check if all questions are answered
function checkIfAllAnswered() {
    if (Object.keys(answers).length === questions.length) {
        document.getElementById('submit-button').style.display = 'block';
    }
}


function prepareAnswers() {
    // Store answers as a JSON string in the hidden input field
    document.getElementById('answers-input').value = JSON.stringify(answers);

    // Disable further changes
    isSubmitted = true;
    document.getElementById('prev-button').classList.add('disabled');
    document.getElementById('next-button').classList.add('disabled');
}

// Function to submit answers
//async function submitAnswers() {
//    // Disable the submit button and navigation buttons
//    document.getElementById('submit-button').style.display = 'none';
//    document.getElementById('prev-button').classList.add('disabled');
//    document.getElementById('next-button').classList.add('disabled');
//
//    // Send answers to the server
//    const response = await fetch('/submit', {
//        method: 'POST',
//        headers: { 'Content-Type': 'application/json' },
//        body: JSON.stringify({ answers })
//    });
//
//    const result = await response.json();
//
//    // Display the result message on the page
//    const resultMessage = document.getElementById('result-message');
//    resultMessage.innerHTML = `Submission successful! Your score: ${result.score}`;
//    resultMessage.style.color = 'green';  // Optionally style the message
//
//    // Prevent further changes
//    isSubmitted = true;
//
//    // Re-render all questions with disabled inputs
//    renderQuestion(currentIndex);
//}
//



// Load questions on page load
window.onload = async function() {
    const response = await fetch('/get_questions');
    const data = await response.json();
    questions = data.questions;``

    renderQuestion(currentIndex);
    renderProgressBar();
    startTimer();  // Start the timer when the page loads
};
