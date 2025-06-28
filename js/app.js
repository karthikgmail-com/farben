// Placeholder for JavaScript code
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded and parsed");

    // Page sections
    const homePage = document.getElementById('home-page');
    const quizPage = document.getElementById('quiz-page');
    const resultPage = document.getElementById('result-page');

    // Homepage elements
    const standardSelect = document.getElementById('standard-select');
    const subjectSelect = document.getElementById('subject-select');
    const lessonSelect = document.getElementById('lesson-select');
    const mixedQuestionsCheckbox = document.getElementById('mixed-questions-checkbox');
    const startQuizBtn = document.getElementById('start-quiz-btn');

    // Quiz Page elements
    const progressIndicator = document.getElementById('progress-indicator');
    const timerDisplay = document.getElementById('timer');
    const quizContent = document.getElementById('quiz-content');
    const submitQuizBtn = document.getElementById('submit-quiz-btn');

    // Result Page elements
    const scoreDisplay = document.getElementById('score');
    const percentageDisplay = document.getElementById('percentage');
    const resultMessage = document.getElementById('result-message');
    const incorrectAnswersList = document.getElementById('incorrect-answers-list');
    const retakeQuizBtn = document.getElementById('retake-quiz-btn');
    const returnHomeBtn = document.getElementById('return-home-btn');
    const confettiContainer = document.getElementById('confetti-container');


    // Dark Mode Toggle
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const sunIcon = document.getElementById('sun-icon');
    const moonIcon = document.getElementById('moon-icon');

    // Check local storage for dark mode preference
    if (localStorage.getItem('darkMode') === 'true' ||
        (!('darkMode' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
        sunIcon.classList.add('hidden');
        moonIcon.classList.remove('hidden');
    } else {
        document.documentElement.classList.remove('dark');
        sunIcon.classList.remove('hidden');
        moonIcon.classList.add('hidden');
    }

    darkModeToggle.addEventListener('click', () => {
        const isDarkMode = document.documentElement.classList.toggle('dark');
        localStorage.setItem('darkMode', isDarkMode);
        sunIcon.classList.toggle('hidden');
        moonIcon.classList.toggle('hidden');
    });

    // --- App State ---
    let currentStandard = '';
    let currentSubject = '';
    let currentLesson = '';
    let isMixedMode = false;
    let questions = [];
    let currentQuestionIndex = 0;
    let score = 0;
    let timerInterval;

    // --- Mock Data Structure (Simulating file system for now) ---
    // In a real scenario with many files, you might fetch a manifest file
    // or use server-side logic to list available subjects/lessons.
    // For GitHub Pages, we'll have to hardcode or fetch directory listings if possible (complex).
    // For now, let's assume we know the structure or fetch a manifest.
    const availableData = {
        "+1": {
            "Physics": ["lesson1", "lesson2"],
            "Chemistry": ["lesson1"]
        },
        "+2": {
            "Physics": ["lesson1"],
            "Chemistry": ["lesson1"]
        }
    };

    // --- Homepage Logic ---
    function updateSubjectOptions() {
        currentStandard = standardSelect.value;
        subjectSelect.innerHTML = '<option value="">-- Select Subject --</option>';
        lessonSelect.innerHTML = '<option value="">-- Select Lesson --</option>';
        subjectSelect.disabled = true;
        lessonSelect.disabled = true;
        startQuizBtn.disabled = true;

        if (currentStandard && availableData[currentStandard]) {
            Object.keys(availableData[currentStandard]).forEach(subject => {
                const option = document.createElement('option');
                option.value = subject.toLowerCase(); // Use lowercase for consistency in paths
                option.textContent = subject;
                subjectSelect.appendChild(option);
            });
            subjectSelect.disabled = false;
        }
    }

    function updateLessonOptions() {
        currentSubject = subjectSelect.value;
        lessonSelect.innerHTML = '<option value="">-- Select Lesson --</option>';
        lessonSelect.disabled = true;
        startQuizBtn.disabled = true;

        if (currentStandard && currentSubject && availableData[currentStandard]) {
            const subjectKey = Object.keys(availableData[currentStandard]).find(k => k.toLowerCase() === currentSubject);
            if (subjectKey && availableData[currentStandard][subjectKey]) {
                availableData[currentStandard][subjectKey].forEach(lessonFile => {
                    const lessonName = lessonFile.replace('.json', ''); // Or format as needed
                    const option = document.createElement('option');
                    option.value = lessonName;
                    option.textContent = `Lesson ${lessonName.replace('lesson', '')}`; // User-friendly name
                    lessonSelect.appendChild(option);
                });
                lessonSelect.disabled = mixedQuestionsCheckbox.checked;
            }
        }
        checkCanStart();
    }

    function toggleLessonSelect() {
        isMixedMode = mixedQuestionsCheckbox.checked;
        lessonSelect.disabled = isMixedMode;
        if (isMixedMode) {
            lessonSelect.value = '';
            currentLesson = '';
        }
        checkCanStart();
    }

    function checkCanStart() {
        currentLesson = lessonSelect.value;
        if (currentStandard && currentSubject && (currentLesson || isMixedMode)) {
            startQuizBtn.disabled = false;
        } else {
            startQuizBtn.disabled = true;
        }
    }

    function resetQuizSelections() {
        standardSelect.value = '';
        subjectSelect.innerHTML = '<option value="">-- Select Subject --</option>';
        subjectSelect.disabled = true;
        lessonSelect.innerHTML = '<option value="">-- Select Lesson --</option>';
        lessonSelect.disabled = true;
        mixedQuestionsCheckbox.checked = false;
        startQuizBtn.disabled = true;
        currentStandard = '';
        currentSubject = '';
        currentLesson = '';
        isMixedMode = false;
    }


    // --- Event Listeners ---
    standardSelect.addEventListener('change', updateSubjectOptions);
    subjectSelect.addEventListener('change', updateLessonOptions);
    lessonSelect.addEventListener('change', checkCanStart);
    mixedQuestionsCheckbox.addEventListener('change', toggleLessonSelect);

    startQuizBtn.addEventListener('click', () => {
        // Navigate to quiz page (logic will be in next step)
        console.log("Starting quiz with:", currentStandard, currentSubject, currentLesson, isMixedMode);
        homePage.classList.add('hidden');
        quizPage.classList.remove('hidden');
        // loadQuestionsAndStart(); // This function will be implemented next
    });

    returnHomeBtn.addEventListener('click', () => {
        resultPage.classList.add('hidden');
        resultPage.classList.remove('slide-in');
        homePage.classList.remove('hidden');
        resetQuizSelections();
    });

    // Initialize
    updateSubjectOptions(); // Initial call in case of pre-filled values (though unlikely here)

    // --- Quiz Logic ---
    let userAnswers = [];

    async function fetchQuestions(standard, subject, lesson) {
        const path = `data/${standard}/${subject}/${lesson}.json`;
        try {
            const response = await fetch(path);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status} for path ${path}`);
            }
            return await response.json();
        } catch (error) {
            console.error("Failed to fetch questions:", error);
            quizContent.innerHTML = `<p class="text-red-500">Error loading questions. Please check the data files or console.</p>`;
            return [];
        }
    }

    async function loadQuestionsAndStart() {
        questions = [];
        userAnswers = [];
        currentQuestionIndex = 0;
        score = 0;
        quizContent.innerHTML = '<p>Loading questions...</p>'; // Loading indicator

        if (isMixedMode) {
            // Fetch from all lessons in the subject
            const subjectKey = Object.keys(availableData[currentStandard]).find(k => k.toLowerCase() === currentSubject);
            if (subjectKey && availableData[currentStandard][subjectKey]) {
                const lessonPromises = availableData[currentStandard][subjectKey].map(lessonFile => {
                    const lessonName = lessonFile.replace('.json', '');
                    return fetchQuestions(currentStandard, currentSubject, lessonName);
                });
                const results = await Promise.all(lessonPromises);
                results.forEach(lessonQuestions => questions.push(...lessonQuestions));
                // Shuffle all questions for mixed mode
                questions.sort(() => Math.random() - 0.5);
            }
        } else {
            questions = await fetchQuestions(currentStandard, currentSubject, currentLesson);
        }

        if (questions.length > 0) {
            userAnswers = new Array(questions.length).fill(null);
            displayQuiz();
            startTimer(questions.length * 4 * 60); // 4 minutes per question
        } else {
            quizContent.innerHTML = `<p class="text-red-500">No questions found for the selected criteria. Please go back and try different options.</p>`;
            // Optionally, disable submit button or provide a back button here
        }
    }

    function displayQuiz() {
        quizContent.innerHTML = ''; // Clear previous content
        questions.forEach((q, index) => {
            const questionElement = document.createElement('div');
            questionElement.classList.add('mb-8', 'p-4', 'border-b', 'dark:border-gray-700');
            questionElement.innerHTML = `
                <h3 class="text-lg font-semibold mb-3">${index + 1}. ${q.question}</h3>
                ${q.image ? `<img src="${q.image}" alt="Question image" class="my-2 max-w-xs rounded-md">` : ''}
                <div class="space-y-2">
                    ${q.options.map((option, i) => `
                        <label for="q${index}_option${i}" class="quiz-option block dark:hover:bg-gray-700 hover:bg-gray-100">
                            <input type="radio" name="question${index}" id="q${index}_option${i}" value="${option}" class="mr-2">
                            ${option}
                        </label>
                    `).join('')}
                </div>
            `;
            quizContent.appendChild(questionElement);

            // Add event listeners for option selection
            const radioButtons = questionElement.querySelectorAll(`input[name="question${index}"]`);
            radioButtons.forEach(radio => {
                radio.addEventListener('change', (event) => {
                    userAnswers[index] = event.target.value;
                    // Update visual selection
                    questionElement.querySelectorAll('.quiz-option').forEach(optLabel => {
                        optLabel.classList.remove('selected', 'dark:bg-blue-700', 'bg-blue-100', 'border-blue-300');
                    });
                    if(event.target.checked) {
                        event.target.parentElement.classList.add('selected', 'dark:bg-blue-700', 'bg-blue-100', 'border-blue-300');
                    }
                    console.log(`Answered q${index}:`, userAnswers[index]);
                });
            });
        });
        updateProgressIndicator();
    }

    function updateProgressIndicator() {
        // This is a single page scrollable test, so progress is more about "X questions loaded"
        // Or we can interpret it as "Question Y of Z" for the timer context
        progressIndicator.textContent = `Total Questions: ${questions.length}`;
    }


    function startTimer(durationInSeconds) {
        clearInterval(timerInterval);
        let timer = durationInSeconds;
        timerInterval = setInterval(() => {
            const minutes = Math.floor(timer / 60);
            const seconds = timer % 60;
            timerDisplay.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            timer--;
            if (timer < 0) {
                clearInterval(timerInterval);
                timerDisplay.textContent = "Time's Up!";
                submitQuiz(true); // Auto-submit
            }
        }, 1000);
    }

    function submitQuiz(isAutoSubmit = false) {
        clearInterval(timerInterval);
        score = 0;
        questions.forEach((q, index) => {
            if (userAnswers[index] === q.answer) {
                score++;
            }
        });

        console.log("Quiz submitted. Score:", score, "out of", questions.length);
        if (!isAutoSubmit) {
            // Could add a confirmation here if desired
        }
        showResults();
    }

    function showResults() {
        quizPage.classList.add('hidden');
        resultPage.classList.remove('hidden');
        resultPage.classList.add('slide-in'); // For animation

        const totalQuestions = questions.length;
        const percentage = totalQuestions > 0 ? Math.round((score / totalQuestions) * 100) : 0;

        scoreDisplay.textContent = `${score} / ${totalQuestions}`;
        percentageDisplay.textContent = `${percentage}%`;

        if (percentage >= 80) {
            resultMessage.textContent = "Excellent! Well done!";
            triggerConfetti();
        } else if (percentage >= 60) {
            resultMessage.textContent = "Good effort! Keep practicing.";
        } else {
            resultMessage.textContent = "Keep practicing! You can improve.";
        }

        incorrectAnswersList.innerHTML = '';
        questions.forEach((q, index) => {
            if (userAnswers[index] !== q.answer) {
                const item = document.createElement('div');
                item.classList.add('mb-4', 'p-3', 'bg-gray-50', 'dark:bg-gray-700', 'rounded-md');
                item.innerHTML = `
                    <p class="font-semibold">${index + 1}. ${q.question}</p>
                    ${q.image ? `<img src="${q.image}" alt="Question image" class="my-1 max-w-xs rounded-md">` : ''}
                    <p>Your answer: <span class="user-answer-incorrect">${userAnswers[index] || "Not answered"}</span></p>
                    <p>Correct answer: <span class="correct-answer-review">${q.answer}</span></p>
                `;
                incorrectAnswersList.appendChild(item);
            }
        });
        if (incorrectAnswersList.innerHTML === '') {
            incorrectAnswersList.innerHTML = '<p>No incorrect answers. Great job!</p>';
        }
    }

    function triggerConfetti() {
        if (typeof confetti === 'function') {
            confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.6 },
                zIndex: 9999 // Ensure confetti is on top
            });
        }
    }

    function resetQuizStateForRetake() {
        questions = [];
        userAnswers = [];
        currentQuestionIndex = 0;
        score = 0;
        clearInterval(timerInterval);
        timerDisplay.textContent = "00:00";
        quizContent.innerHTML = '';
        progressIndicator.textContent = '';
        resultPage.classList.add('hidden');
        resultPage.classList.remove('slide-in');
        // Selections (standard, subject, etc.) are kept for retake
    }


    // --- Update Event Listeners ---
    startQuizBtn.addEventListener('click', () => {
        console.log("Starting quiz with:", currentStandard, currentSubject, currentLesson, isMixedMode);
        homePage.classList.add('hidden');
        quizPage.classList.remove('hidden');
        resultPage.classList.add('hidden'); // Ensure result page is hidden
        resultPage.classList.remove('slide-in');
        loadQuestionsAndStart();
    });

    submitQuizBtn.addEventListener('click', () => submitQuiz(false));

    retakeQuizBtn.addEventListener('click', () => {
        resetQuizStateForRetake();
        // Navigate back to quiz page and reload questions
        quizPage.classList.remove('hidden');
        loadQuestionsAndStart();
    });

    // --- Placeholder for future functions ---
    // function displayQuestion(index) {} // Replaced by displayQuiz for full scrollable list
});
