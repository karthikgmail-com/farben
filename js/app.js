document.addEventListener('DOMContentLoaded', () => {
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
    // const timerDisplay = document.getElementById('timer'); // Old text timer
    const timerSvgProgress = document.getElementById('timer-svg-progress');
    const timerTextDisplay = document.getElementById('timer-text');
    const quizContent = document.getElementById('quiz-content');
    const submitQuizBtn = document.getElementById('submit-quiz-btn');

    // Result Page elements
    const scoreDisplay = document.getElementById('score');
    const percentageDisplay = document.getElementById('percentage');
    const resultMessage = document.getElementById('result-message');
    const incorrectAnswersList = document.getElementById('incorrect-answers-list');
    const motivationalQuoteElement = document.getElementById('motivational-quote').querySelector('p'); // Get the p tag
    const retakeQuizBtn = document.getElementById('retake-quiz-btn');
    const returnHomeBtn = document.getElementById('return-home-btn');

    // Motivational Quotes
    const motivationalQuotes = [
        "The expert in anything was once a beginner.",
        "Don't watch the clock; do what it does. Keep going.",
        "The only way to do great work is to love what you do.",
        "Believe you can and you're halfway there.",
        "The harder you work for something, the greater you'll feel when you achieve it.",
        "Success is not final, failure is not fatal: It is the courage to continue that counts.",
        "Push yourself, because no one else is going to do it for you.",
        "Your limitation—it’s only your imagination."
    ];

    // Dark Mode Toggle
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const sunIcon = darkModeToggle.querySelector('#sun-icon');
    const moonIcon = darkModeToggle.querySelector('#moon-icon');

    function setDarkMode(isDark) {
        if (isDark) {
            document.documentElement.classList.add('dark');
            sunIcon.classList.add('hidden');
            moonIcon.classList.remove('hidden');
            localStorage.setItem('darkMode', 'true');
        } else {
            document.documentElement.classList.remove('dark');
            sunIcon.classList.remove('hidden');
            moonIcon.classList.add('hidden');
            localStorage.setItem('darkMode', 'false');
        }
    }

    if (localStorage.getItem('darkMode') === 'true' ||
        (!('darkMode' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        setDarkMode(true);
    } else {
        setDarkMode(false);
    }

    darkModeToggle.addEventListener('click', () => {
        const isDarkMode = document.documentElement.classList.contains('dark');
        setDarkMode(!isDarkMode);
    });

    // --- App State ---
    let currentStandard = '';
    let currentSubject = '';
    let currentLesson = '';
    let isMixedMode = false;
    let questions = [];
    let userAnswers = [];
    let score = 0;
    let timerInterval;

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
                option.value = subject.toLowerCase();
                option.textContent = subject;
                subjectSelect.appendChild(option);
            });
            subjectSelect.disabled = false;
        }
        checkCanStart();
    }

    function updateLessonOptions() {
        currentSubject = subjectSelect.value;
        lessonSelect.innerHTML = '<option value="">-- Select Lesson --</option>';
        lessonSelect.disabled = true;

        if (currentStandard && currentSubject && availableData[currentStandard]) {
            const subjectKeyOriginal = Object.keys(availableData[currentStandard]).find(k => k.toLowerCase() === currentSubject);
            if (subjectKeyOriginal && availableData[currentStandard][subjectKeyOriginal]) {
                availableData[currentStandard][subjectKeyOriginal].forEach(lessonFile => {
                    const lessonName = lessonFile.replace('.json', '');
                    const option = document.createElement('option');
                    option.value = lessonName;
                    option.textContent = `Lesson ${lessonName.replace('lesson', '')}`;
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
        } else if(lessonSelect.options.length > 1 && currentSubject) {
             lessonSelect.disabled = false;
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

    async function fetchQuestions(std, subj, less) {
        const path = `data/${std}/${subj}/${less}.json`;
        try {
            const response = await fetch(path);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status} for ${path}`);
            return await response.json();
        } catch (error) {
            console.error("Failed to fetch questions:", error);
            quizContent.innerHTML = `<p class="text-red-500 dark:text-red-400 p-4">Error loading questions. Please check data file or console.</p>`;
            return [];
        }
    }

    async function loadQuestionsAndStart() {
        questions = [];
        userAnswers = [];
        score = 0;
        quizContent.innerHTML = '<p class="text-center p-4">Loading questions...</p>';

        if (isMixedMode) {
            const subjectKeyOriginal = Object.keys(availableData[currentStandard]).find(k => k.toLowerCase() === currentSubject);
            if (subjectKeyOriginal && availableData[currentStandard][subjectKeyOriginal]) {
                const lessonPromises = availableData[currentStandard][subjectKeyOriginal].map(lessonFile => {
                    const lessonName = lessonFile.replace('.json', '');
                    return fetchQuestions(currentStandard, currentSubject, lessonName);
                });
                const results = await Promise.all(lessonPromises);
                results.forEach(lessonQuestions => questions.push(...lessonQuestions));
                questions.sort(() => Math.random() - 0.5);
            }
        } else {
            questions = await fetchQuestions(currentStandard, currentSubject, currentLesson);
        }

        if (questions.length > 0) {
            userAnswers = new Array(questions.length).fill(null);
            displayQuiz();
            startTimer(questions.length * 4 * 60); // 4 minutes per question
        } else if (quizContent.innerHTML.includes('Loading questions...')) {
            quizContent.innerHTML = `<p class="text-center p-4 text-red-500 dark:text-red-400">No questions found. Please try different options.</p>`;
            submitQuizBtn.disabled = true;
        }
         progressIndicator.textContent = `Total Questions: ${questions.length}`;
    }

    function displayQuiz() {
        quizContent.innerHTML = '';
        submitQuizBtn.disabled = questions.length === 0;

        questions.forEach((q, index) => {
            const questionId = `q_${index}`;
            const questionElement = document.createElement('div');
            questionElement.classList.add('mb-8', 'p-4', 'border-b', 'border-gray-200', 'dark:border-gray-700');

            let imageHTML = '';
            if (q.image) {
                imageHTML = `<img src="${q.image}" alt="Question image ${index + 1}" class="my-2 max-w-xs rounded-md shadow-sm mx-auto sm:mx-0">`;
            }

            // Question and options are plain text, no atob() needed here for this reverted version
            questionElement.innerHTML = `
                <h3 class="text-lg font-semibold mb-3 text-gray-800 dark:text-gray-200">${index + 1}. ${q.question}</h3>
                ${imageHTML}
                <div class="space-y-2 mt-2">
                    ${q.options.map((option, i) => `
                        <label for="${questionId}_option${i}" class="quiz-option">
                            <input type="radio" name="${questionId}" id="${questionId}_option${i}" value="${option}" class="mr-2 sr-only">
                            <span class="option-text">${option}</span>
                        </label>
                    `).join('')}
                </div>
            `;
            quizContent.appendChild(questionElement);

            const radioLabels = questionElement.querySelectorAll('.quiz-option');
            radioLabels.forEach(label => {
                label.addEventListener('click', (event) => {
                    const associatedRadio = label.querySelector('input[type="radio"]');
                    if (associatedRadio) {
                        associatedRadio.checked = true;
                        userAnswers[index] = associatedRadio.value;

                        questionElement.querySelectorAll('.quiz-option').forEach(optLabel => {
                            optLabel.classList.remove('selected', 'font-semibold');
                        });
                        label.classList.add('selected', 'font-semibold');
                    }
                });
            });
        });
    }

    function startTimer(durationInSeconds) {
        clearInterval(timerInterval);
        let timeLeft = durationInSeconds;
        const totalDuration = durationInSeconds;

        const radius = timerSvgProgress.r.baseVal.value;
        const circumference = 2 * Math.PI * radius;
        timerSvgProgress.style.strokeDasharray = circumference;
        timerSvgProgress.style.strokeDashoffset = 0; // Start full
        timerSvgProgress.classList.remove('warning', 'danger');


        timerInterval = setInterval(() => {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            timerTextDisplay.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

            const progress = timeLeft / totalDuration;
            timerSvgProgress.style.strokeDashoffset = circumference * (1 - progress);

            if (timeLeft <= totalDuration * 0.25) {
                timerSvgProgress.classList.add('danger');
                timerSvgProgress.classList.remove('warning');
            } else if (timeLeft <= totalDuration * 0.5) {
                timerSvgProgress.classList.add('warning');
                timerSvgProgress.classList.remove('danger');
            } else {
                timerSvgProgress.classList.remove('warning', 'danger');
            }

            timeLeft--;
            if (timeLeft < 0) {
                clearInterval(timerInterval);
                timerTextDisplay.textContent = "00:00";
                timerSvgProgress.style.strokeDashoffset = circumference;
                timerSvgProgress.classList.add('danger');
                // timerDisplay.textContent = "Time's Up!"; // Old way
                submitQuiz(true);
            }
        }, 1000);
    }

    function submitQuiz(isAutoSubmit = false) {
        clearInterval(timerInterval);
        score = 0;
        questions.forEach((q, index) => {
            // No atob() needed for q.answer in this reverted version
            if (userAnswers[index] === q.answer) {
                score++;
            }
        });
        if (!isAutoSubmit) {
            // console.log("Manual submit");
        }
        showResults();
    }

    function showResults() {
        homePage.classList.add('hidden');
        quizPage.classList.add('hidden');
        resultPage.classList.remove('hidden');

        const resultCard = resultPage.querySelector('.card');
        if (resultCard) { // Ensure card exists before trying to manipulate classList
            resultCard.classList.remove('slide-in');
            void resultCard.offsetWidth;
            resultCard.classList.add('slide-in');
        }

        const totalQuestions = questions.length;
        const percentage = totalQuestions > 0 ? Math.round((score / totalQuestions) * 100) : 0;

        scoreDisplay.textContent = `${score} / ${totalQuestions}`;
        percentageDisplay.textContent = `${percentage}%`;

        if (percentage >= 80) {
            resultMessage.textContent = "Excellent! Well done!";
            if (typeof confetti === 'function') confetti({ particleCount: 150, spread: 90, origin: { y: 0.6 }, zIndex: 10000 });
        } else if (percentage >= 60) {
            resultMessage.textContent = "Good effort! Keep practicing.";
        } else {
            resultMessage.textContent = "Keep practicing! You can improve.";
        }

        // Display a random motivational quote
        const randomIndex = Math.floor(Math.random() * motivationalQuotes.length);
        motivationalQuoteElement.textContent = `"${motivationalQuotes[randomIndex]}"`;

        incorrectAnswersList.innerHTML = '';
        let hasIncorrect = false;
        questions.forEach((q, index) => {
            if (userAnswers[index] !== q.answer) {
                hasIncorrect = true;
                const item = document.createElement('div');
                item.classList.add('mb-4', 'p-3', 'bg-gray-50', 'dark:bg-gray-700', 'rounded-md', 'shadow-sm');
                let imageReviewHTML = '';
                if (q.image) {
                    imageReviewHTML = `<img src="${q.image}" alt="Question image ${index + 1}" class="my-1 max-w-xs rounded-md mx-auto sm:mx-0">`;
                }
                // No atob() for q.question or q.answer
                item.innerHTML = `
                    <p class="font-semibold text-gray-800 dark:text-gray-200">${index + 1}. ${q.question}</p>
                    ${imageReviewHTML}
                    <p class="text-sm">Your answer: <span class="user-answer-incorrect">${userAnswers[index] || "Not answered"}</span></p>
                    <p class="text-sm">Correct answer: <span class="correct-answer-review">${q.answer}</span></p>
                `;
                incorrectAnswersList.appendChild(item);
            }
        });
        if (!hasIncorrect && totalQuestions > 0) {
            incorrectAnswersList.innerHTML = '<p class="text-green-600 dark:text-green-400">Congratulations! No incorrect answers.</p>';
        } else if (totalQuestions === 0) {
             incorrectAnswersList.innerHTML = '<p>No questions were loaded for this quiz.</p>';
        }
    }

    function resetQuizStateForRetake() {
        userAnswers = new Array(questions.length).fill(null);
        score = 0;
        clearInterval(timerInterval);
        timerTextDisplay.textContent = "00:00"; // Reset new timer text
        if (timerSvgProgress && timerSvgProgress.r && timerSvgProgress.r.baseVal) { // Check if SVG timer elements exist
            const radius = timerSvgProgress.r.baseVal.value;
            const circumference = 2 * Math.PI * radius;
            timerSvgProgress.style.strokeDashoffset = 0; // Full circle
            timerSvgProgress.classList.remove('warning', 'danger');
        }
        quizContent.innerHTML = '';
        resultPage.classList.add('hidden');
        const resultCard = resultPage.querySelector('.card');
        if(resultCard) resultCard.classList.remove('slide-in');
    }

    // --- Event Listeners ---
    standardSelect.addEventListener('change', updateSubjectOptions);
    subjectSelect.addEventListener('change', updateLessonOptions);
    lessonSelect.addEventListener('change', checkCanStart);
    mixedQuestionsCheckbox.addEventListener('change', toggleLessonSelect);

    startQuizBtn.addEventListener('click', () => {
        homePage.classList.add('hidden');
        quizPage.classList.remove('hidden');
        resultPage.classList.add('hidden');
        const resultCard = resultPage.querySelector('.card');
        if(resultCard) resultCard.classList.remove('slide-in');
        loadQuestionsAndStart();
    });

    submitQuizBtn.addEventListener('click', () => submitQuiz(false));

    retakeQuizBtn.addEventListener('click', () => {
        resetQuizStateForRetake();
        quizPage.classList.remove('hidden');
        homePage.classList.add('hidden');
        loadQuestionsAndStart();
    });

    returnHomeBtn.addEventListener('click', () => {
        resultPage.classList.add('hidden');
        const resultCard = resultPage.querySelector('.card');
        if(resultCard) resultCard.classList.remove('slide-in');
        homePage.classList.remove('hidden');
        resetQuizSelections();
    });

    // Initialize
    updateSubjectOptions();
    homePage.classList.remove('hidden');
    quizPage.classList.add('hidden');
    resultPage.classList.add('hidden');
});
