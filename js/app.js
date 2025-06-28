document.addEventListener('DOMContentLoaded', () => {
    // Page sections
    const homePage = document.getElementById('home-page');
    const quizPage = document.getElementById('quiz-page');
    const resultPage = document.getElementById('result-page');

    // Homepage elements
    // Revert to actual select dropdowns
    const standardSelect = document.getElementById('standard-select');
    const subjectSelect = document.getElementById('subject-select');
    const lessonSelect = document.getElementById('lesson-select');

    const mixedQuestionsCheckbox = document.getElementById('mixed-questions-checkbox');
    const startQuizBtn = document.getElementById('start-quiz-btn');

    // Quiz Page elements
    const progressIndicator = document.getElementById('progress-indicator');
    // const timerDisplay = document.getElementById('timer'); // Old timer text element
    const timerWrapper = document.getElementById('timer-wrapper'); // New
    const timerSvgProgress = document.getElementById('timer-svg-progress'); // New
    const timerTextDisplay = document.getElementById('timer-text'); // New for text inside SVG
    const quizContent = document.getElementById('quiz-content');
    const submitQuizBtn = document.getElementById('submit-quiz-btn');

    // Result Page elements
    const scoreDisplay = document.getElementById('score');
    const percentageDisplay = document.getElementById('percentage');
    const resultMessage = document.getElementById('result-message');
    const incorrectAnswersList = document.getElementById('incorrect-answers-list');
    const retakeQuizBtn = document.getElementById('retake-quiz-btn');
    const returnHomeBtn = document.getElementById('return-home-btn');
    // const confettiContainer = document.getElementById('confetti-container'); // Already available globally

    // Dark Mode Toggle
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const sunIcon = darkModeToggle.querySelector('#sun-icon'); // More specific selection
    const moonIcon = darkModeToggle.querySelector('#moon-icon'); // More specific selection

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

    // Check local storage for dark mode preference
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
    let currentStandard = ''; // Will be set from standardSelectInput.value
    let currentSubject = '';  // Will be set from subjectSelectInput.value
    let currentLesson = '';
    let isMixedMode = false;
    let questions = [];
    // let currentQuestionIndex = 0; // Not used in a scrollable list manner for indexing
    let userAnswers = []; // To store user's answers
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

    // Reverted Homepage Logic (using dropdowns)
    function updateSubjectOptions() {
        currentStandard = standardSelect.value; // From actual select
        subjectSelect.innerHTML = '<option value="">-- Select Subject --</option>';
        lessonSelect.innerHTML = '<option value="">-- Select Lesson --</option>';
        subjectSelect.disabled = true;
        lessonSelect.disabled = true;
        startQuizBtn.disabled = true;

        if (currentStandard && availableData[currentStandard]) {
            Object.keys(availableData[currentStandard]).forEach(subjectName => {
                const option = document.createElement('option');
                option.value = subjectName.toLowerCase();
                option.textContent = subjectName;
                subjectSelect.appendChild(option);
            });
            subjectSelect.disabled = false;
        }
        checkCanStart();
    }

    function updateLessonOptions() {
        currentSubject = subjectSelect.value; // From actual select
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

    mixedQuestionsCheckbox.addEventListener('change', () => {
        isMixedMode = mixedQuestionsCheckbox.checked;
        lessonSelect.disabled = isMixedMode;
        if (isMixedMode) {
            lessonSelect.value = '';
            currentLesson = '';
        } else if(lessonSelect.options.length > 1 && currentSubject) { // Check if subject selected
             lessonSelect.disabled = false;
        }
        checkCanStart();
    });

    lessonSelect.addEventListener('change', () => {
        currentLesson = lessonSelect.value;
        checkCanStart();
    });

    function checkCanStart() {
        // currentStandard and currentSubject are from select dropdowns
        // currentLesson is from lessonSelect dropdown
        if (currentStandard && currentSubject && (currentLesson || isMixedMode)) {
            startQuizBtn.disabled = false;
        } else {
            startQuizBtn.disabled = true;
        }
    }

    function resetQuizSelections() {
        currentStandard = '';
        currentSubject = '';
        currentLesson = '';
        isMixedMode = false;

        standardSelect.value = ''; // Reset actual select
        subjectSelect.innerHTML = '<option value="">-- Select Subject --</option>';
        subjectSelect.disabled = true;

        lessonSelect.innerHTML = '<option value="">-- Select Lesson --</option>';
        lessonSelect.disabled = true;

        mixedQuestionsCheckbox.checked = false;
        startQuizBtn.disabled = true;
    }

    // Event listeners for original dropdowns
    standardSelect.addEventListener('change', updateSubjectOptions);
    subjectSelect.addEventListener('change', updateLessonOptions);
    // lessonSelect and mixedQuestionsCheckbox listeners are already above


    async function fetchQuestions(std, subj, less) {
        const path = `data/${std}/${subj}/${less}.json`;
        try {
            const response = await fetch(path);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status} for ${path}`);
            return await response.json();
        } catch (error) {
            console.error("Failed to fetch questions:", error);
            quizContent.innerHTML = `<p class="text-red-500 dark:text-red-400 p-4">Error loading questions for ${subj} ${less}. Please check data file exists and is valid JSON or console for more details.</p>`;
            return [];
        }
    }

    async function loadQuestionsAndStart() {
        questions = [];
        userAnswers = []; // Reset user answers
        score = 0; // Reset score
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
                questions.sort(() => Math.random() - 0.5); // Shuffle for mixed mode
            }
        } else {
            questions = await fetchQuestions(currentStandard, currentSubject, currentLesson);
        }

        if (questions.length > 0) {
            userAnswers = new Array(questions.length).fill(null); // Initialize userAnswers array
            displayQuiz();
            startTimer(questions.length * 4 * 60);
        } else if (quizContent.innerHTML.includes('Loading questions...')) { // Only update if not already showing an error
            quizContent.innerHTML = `<p class="text-center p-4 text-red-500 dark:text-red-400">No questions found for the selected criteria. Please try different options.</p>`;
            submitQuizBtn.disabled = true; // Disable submit if no questions
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

            let decodedQuestion = "Error: Could not decode question.";
            try {
                decodedQuestion = atob(q.question);
            } catch (e) {
                console.error("Error decoding question text:", q.question, e);
            }

            questionElement.innerHTML = `
                <h3 class="text-lg font-semibold mb-3 text-gray-800 dark:text-gray-200">${index + 1}. ${decodedQuestion}</h3>
                ${imageHTML}
                <div class="space-y-2 mt-2">
                    ${q.options.map((encodedOption, i) => {
                        let decodedOption = "Error: Could not decode option.";
                        try {
                            decodedOption = atob(encodedOption);
                        } catch (e) {
                            console.error("Error decoding option:", encodedOption, e);
                        }
                        return `
                        <label for="${questionId}_option${i}" class="quiz-option">
                            <input type="radio" name="${questionId}" id="${questionId}_option${i}" value="${decodedOption}" class="mr-2 sr-only">
                            <span class="option-text">${decodedOption}</span>
                        </label>
                        `;
                    }).join('')}
                </div>
            `;
            quizContent.appendChild(questionElement);

            // Add event listeners for option selection
            const radioLabels = questionElement.querySelectorAll('.quiz-option');
            radioLabels.forEach(label => {
                label.addEventListener('click', (event) => {
                    const associatedRadio = label.querySelector('input[type="radio"]');
                    if (associatedRadio) {
                        associatedRadio.checked = true;
                        // userAnswers[index] should store the decoded value, which is already set as radio's value
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
        const totalDuration = durationInSeconds; // Keep initial duration

        const radius = timerSvgProgress.r.baseVal.value;
        const circumference = 2 * Math.PI * radius;
        timerSvgProgress.style.strokeDasharray = circumference;

        // Initial full circle
        timerSvgProgress.style.strokeDashoffset = 0;
        timerSvgProgress.classList.remove('warning', 'danger');


        timerInterval = setInterval(() => {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            timerTextDisplay.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

            // Update SVG progress
            const progress = timeLeft / totalDuration;
            timerSvgProgress.style.strokeDashoffset = circumference * (1 - progress);

            // Optional: Change color based on time left
            if (timeLeft <= totalDuration * 0.25) { // Last 25% of time
                timerSvgProgress.classList.add('danger');
                timerSvgProgress.classList.remove('warning');
            } else if (timeLeft <= totalDuration * 0.5) { // Last 50% of time
                timerSvgProgress.classList.add('warning');
                timerSvgProgress.classList.remove('danger');
            } else {
                timerSvgProgress.classList.remove('warning', 'danger');
            }

            timeLeft--;
            if (timeLeft < 0) {
                clearInterval(timerInterval);
                timerTextDisplay.textContent = "00:00"; // Ensure it shows 00:00 at the end
                timerSvgProgress.style.strokeDashoffset = circumference; // Empty circle
                timerSvgProgress.classList.add('danger'); // Ensure danger color at timeout
                // Optionally, add a more prominent "Time's Up!" message near timer or globally
                // For now, the visual and 00:00 is the indicator.
                submitQuiz(true); // Auto-submit
            }
        }, 1000);
    }

    function submitQuiz(isAutoSubmit = false) {
        clearInterval(timerInterval); // Ensure timer is stopped on any submission
        score = 0;
        questions.forEach((q, index) => {
            try {
                const correctAnswer = atob(q.answer); // Decode Base64 answer
                if (userAnswers[index] === correctAnswer) {
                    score++;
                }
            } catch (e) {
                console.error("Error decoding answer for question:", q.question, e);
                // Handle error: maybe this question is skipped for scoring or marked specially
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

        // Ensure the result card has the slide-in animation
        const resultCard = resultPage.querySelector('.max-w-lg'); // The card div
        resultCard.classList.remove('slide-in'); // Remove if already there to re-trigger
        void resultCard.offsetWidth; // Force reflow to allow re-triggering animation
        resultCard.classList.add('slide-in');


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
                let decodedQuestionForReview = "Error: Could not decode question text.";
                try {
                    // q.question is still encoded here as it comes from the original 'questions' array
                    decodedQuestionForReview = atob(q.question);
                } catch (e) {
                    console.error("Error decoding question for review:", q.question, e);
                }

                let correctAnswerForReview = "Error: Could not decode answer.";
                try {
                    correctAnswerForReview = atob(q.answer); // Decode for display
                } catch (e) {
                    // Error already logged in submitQuiz, but good to be safe or if called independently
                    console.error("Error decoding answer for review (already logged?):", q.answer, e);
                }
                item.innerHTML = `
                    <p class="font-semibold text-gray-800 dark:text-gray-200">${index + 1}. ${decodedQuestionForReview}</p>
                    ${imageReviewHTML}
                    <p class="text-sm">Your answer: <span class="user-answer-incorrect">${userAnswers[index] || "Not answered"}</span></p>
                    <p class="text-sm">Correct answer: <span class="correct-answer-review">${correctAnswerForReview}</span></p>
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
        // questions array and selections (standard, subject, lesson, mixedMode) are preserved
        userAnswers = new Array(questions.length).fill(null);
        score = 0;
        clearInterval(timerInterval);
        timerTextDisplay.textContent = "00:00"; // Reset new timer text
        if(timerSvgProgress) { // Reset SVG progress
            const radius = timerSvgProgress.r.baseVal.value;
            const circumference = 2 * Math.PI * radius;
            timerSvgProgress.style.strokeDashoffset = 0; // Full circle
            timerSvgProgress.classList.remove('warning', 'danger');
        }
        quizContent.innerHTML = ''; // Will be repopulated by loadQuestionsAndStart
        // progressIndicator.textContent = ''; // Will be repopulated
        resultPage.classList.add('hidden');
        const resultCard = resultPage.querySelector('.max-w-lg');
        if(resultCard) resultCard.classList.remove('slide-in');
    }

    // --- Event Listeners ---
    standardSelect.addEventListener('change', updateSubjectOptions);
    subjectSelect.addEventListener('change', updateLessonOptions);
    lessonSelect.addEventListener('change', checkCanStart); // Added to re-check when lesson changes
    mixedQuestionsCheckbox.addEventListener('change', toggleLessonSelect);

    startQuizBtn.addEventListener('click', () => {
        homePage.classList.add('hidden');
        quizPage.classList.remove('hidden');
        resultPage.classList.add('hidden');
        const resultCard = resultPage.querySelector('.max-w-lg');
        if(resultCard) resultCard.classList.remove('slide-in');
        loadQuestionsAndStart();
    });

    submitQuizBtn.addEventListener('click', () => submitQuiz(false));

    retakeQuizBtn.addEventListener('click', () => {
        resetQuizStateForRetake();
        quizPage.classList.remove('hidden'); // Show quiz page again
        homePage.classList.add('hidden');    // Ensure home is hidden
        loadQuestionsAndStart(); // Reload same questions and restart timer
    });

    returnHomeBtn.addEventListener('click', () => {
        resultPage.classList.add('hidden');
        const resultCard = resultPage.querySelector('.max-w-lg');
        if(resultCard) resultCard.classList.remove('slide-in');
        homePage.classList.remove('hidden');
        resetQuizSelections();
    });

    // Initialize
    updateSubjectOptions(); // Initial call
    homePage.classList.remove('hidden'); // Ensure home page is visible on load
    quizPage.classList.add('hidden');
    resultPage.classList.add('hidden');
});
