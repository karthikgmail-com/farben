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
    const customQuizSizeContainer = document.getElementById('custom-quiz-size-container');
    const customQuizSizeInput = document.getElementById('custom-quiz-size');
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

    // Consolidated Motivational Quotes
    const motivationalQuotes = [
        "\"I trained 4 years to run 9 seconds and people give up after 2 months.\" — Usain Bolt",
        "\"We’re not here to take part. We’re here to take over.\" — Conor McGregor",
        "\"Be uncommon among uncommon people.\" — David Goggins",
        "\"I’m the most brutal and most vicious champion there’s ever been.\" — Mike Tyson",
        "\"I know I’m the best. I prove it every day.\" — Cristiano Ronaldo",
        "\"I am the greatest. I said that before I knew I was.\" — Muhammad Ali",
        "\"I saw myself being a champion long before I was.\" — Arnold Schwarzenegger",
        "\"Be the hardest worker in the room.\" — Dwayne ‘The Rock’ Johnson",
        "\"Some people want it to happen, some wish it would happen, others make it happen.\" — Michael Jordan",
        "\"Discipline equals freedom.\" — Jocko Willink",
        "\"I didn’t come this far to only come this far.\" — Tom Brady",
        "\"I came like a king, left like a legend.\" — Zlatan Ibrahimović",
        "\"If you want to take the island, burn the f**ing boats.\" — Tony Robbins", // Note: Asterisk added for safety
        "\"I just want to be better every day.\" — Neymar Jr",
        "\"I’m not the MVP because of numbers. I’m the MVP because I never quit.\" — Giannis Antetokounmpo",
        "\"Your love makes me strong. Your hate makes me unstoppable.\" — Cristiano Ronaldo",
        "\"I don’t think limits.\" — Usain Bolt",
        "\"When you think you’re done, you’re only at 40%.\" — David Goggins",
        "\"Fear is the greatest obstacle to learning. But fear is also your best friend.\" — Mike Tyson",
        "\"Talent without working hard is nothing.\" — Cristiano Ronaldo",
        "\"I'm young. I'm handsome. I'm fast. I can't possibly be beat.\" — Muhammad Ali",
        "\"You can’t climb the ladder of success with your hands in your pockets.\" — Arnold Schwarzenegger",
        "\"Success at anything will always come down to this: focus and effort. And we control both.\" — The Rock",
        "\"I never lost a game. I just ran out of time.\" — Michael Jordan",
        "\"Good. You failed? Good. Now learn. Adjust. Get stronger.\" — Jocko Willink",
        "\"You push your body to the limits, but it’s the mind that breaks first.\" — Tom Brady",
        "\"Lions don’t compare themselves to humans.\" — Zlatan Ibrahimović",
        "\"Where focus goes, energy flows.\" — Tony Robbins",
        "\"Pressure? What pressure? It’s my job. I love it.\" — Neymar Jr",
        "\"I stay locked in. I’m obsessed with improvement.\" — Giannis Antetokounmpo",
        "\"There are better starters than me, but I’m a strong finisher.\" — Usain Bolt",
        "\"The most powerful weapon you have is your mind. Train it.\" — David Goggins",
        "\"Everyone has a plan until they get punched in the mouth.\" — Mike Tyson",
        "\"I don’t chase records. Records chase me.\" — Cristiano Ronaldo",
        "\"It’s not bragging if you can back it up.\" — Muhammad Ali",
        "\"Forget plan B. Plan A is all that matters.\" — Arnold Schwarzenegger",
        "\"Blood, sweat, and respect. First two you give. Last one you earn.\" — The Rock",
        "\"Once I made a decision, I never thought about it again.\" — Michael Jordan",
        "\"Get after it. Every day. No matter what.\" — Jocko Willink",
        "\"Every second counts. Don’t waste one.\" — Tom Brady",
        "\"They bought a Ferrari and drove it like a Fiat.\" — Zlatan Ibrahimović",
        "\"The only limit to your impact is your imagination and commitment.\" — Tony Robbins",
        "\"Every day, I train like I’m starting from zero.\" — Neymar Jr",
        "\"I work to be legendary.\" — Giannis Antetokounmpo",
        "\"Why lie? I’m not going to be a hypocrite. I’m better than the rest.\" — Cristiano Ronaldo",
        "\"Kill them with success. Bury them with a smile.\" — Usain Bolt",
        "\"You will never learn from people if you always tap out when it gets hard.\" — David Goggins",
        "\"Real freedom is having nothing. I was freer when I didn’t have a cent.\" — Mike Tyson",
        "\"I see myself as the best footballer in the world.\" — Cristiano Ronaldo",
        "\"If my mind can conceive it and my heart can believe it – then I can achieve it.\" — Muhammad Ali"
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
            "Chemistry": ["lesson1", "lesson2", "lesson3", "lesson4", "lesson5", "lesson6", "lesson7"]
        }
    };

    function updateSubjectOptions() {
        console.log("updateSubjectOptions called");
        currentStandard = standardSelect.value;
        console.log("Current standard selected:", currentStandard);

        subjectSelect.innerHTML = '<option value="">-- Select Subject --</option>';
        lessonSelect.innerHTML = '<option value="">-- Select Lesson --</option>';
        subjectSelect.disabled = true;
        lessonSelect.disabled = true;
        customQuizSizeContainer.classList.add('hidden'); // Also hide this when standard changes
        startQuizBtn.disabled = true;

        if (currentStandard && availableData[currentStandard]) {
            console.log("Subjects for standard '" + currentStandard + "':", Object.keys(availableData[currentStandard]));
            Object.keys(availableData[currentStandard]).forEach(subject => {
                console.log("Adding subject:", subject);
                const option = document.createElement('option');
                option.value = subject.toLowerCase();
                option.textContent = subject;
                subjectSelect.appendChild(option);
            });
            subjectSelect.disabled = false;
            console.log("Subject select enabled.");
        } else {
            console.log("No valid standard selected or no data for standard:", currentStandard);
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
            customQuizSizeContainer.classList.remove('hidden');
            lessonSelect.value = '';
            currentLesson = '';
        } else {
            customQuizSizeContainer.classList.add('hidden');
            if(lessonSelect.options.length > 1 && currentSubject) {
                 lessonSelect.disabled = false;
            }
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
                questions.sort(() => Math.random() - 0.5); // Shuffle all fetched questions

                let numQuestionsToLoad = parseInt(customQuizSizeInput.value, 10);
                if (isNaN(numQuestionsToLoad) || numQuestionsToLoad < parseInt(customQuizSizeInput.min, 10) || numQuestionsToLoad > parseInt(customQuizSizeInput.max, 10)) {
                    numQuestionsToLoad = 25; // Default to 25 if input is invalid or out of range
                    customQuizSizeInput.value = "25"; // Reset input to default
                }

                if (questions.length > numQuestionsToLoad) {
                    questions = questions.slice(0, numQuestionsToLoad);
                }
                // If questions.length is less than numQuestionsToLoad, all available questions will be used.
            }
        } else {
            questions = await fetchQuestions(currentStandard, currentSubject, currentLesson);
        }

        if (questions.length > 0) {
            userAnswers = new Array(questions.length).fill(null);
            displayQuiz();
            startTimer(questions.length * 2 * 60); // 2 minutes per question
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
            const questionHeadingId = `question-heading-${index}`;
            questionElement.innerHTML = `
                <h3 id="${questionHeadingId}" class="text-lg font-semibold mb-3 text-gray-800 dark:text-gray-200">${index + 1}. ${q.question}</h3>
                ${imageHTML}
                <div role="radiogroup" aria-labelledby="${questionHeadingId}" class="space-y-2 mt-2">
                    ${q.options.map((option, i) => `
                        <label for="${questionId}_option${i}" class="quiz-option" tabindex="0" role="radio" aria-checked="false">
                            <input type="radio" name="${questionId}" id="${questionId}_option${i}" value="${option}" class="mr-2 sr-only">
                            <span class="option-text">${option}</span>
                        </label>
                    `).join('')}
                </div>
            `;
            quizContent.appendChild(questionElement);

            const radioLabels = questionElement.querySelectorAll('.quiz-option');
            const radioInputs = questionElement.querySelectorAll('input[type="radio"]');

            radioLabels.forEach((label, labelIndex) => {
                const associatedRadio = radioInputs[labelIndex]; // More direct association

                const selectOption = () => {
                    // Uncheck all radios in this group and update ARIA attributes
                    radioInputs.forEach((radio, radioIdx) => {
                        radio.checked = false;
                        radioLabels[radioIdx].classList.remove('selected', 'font-semibold');
                        radioLabels[radioIdx].setAttribute('aria-checked', 'false');
                    });

                    // Check the selected one
                    associatedRadio.checked = true;
                    userAnswers[index] = associatedRadio.value;
                    label.classList.add('selected', 'font-semibold');
                    label.setAttribute('aria-checked', 'true');
                };

                label.addEventListener('click', selectOption);

                label.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault(); // Prevent space from scrolling page
                        selectOption();
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
        window.scrollTo(0, 0); // Scroll to top when results page is shown

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

        // Display a random motivational quote from the consolidated list
        if (motivationalQuotes.length > 0) {
            const randomIndex = Math.floor(Math.random() * motivationalQuotes.length);
            motivationalQuoteElement.textContent = motivationalQuotes[randomIndex]; // Quotes already include " " and author
        } else {
            motivationalQuoteElement.textContent = ""; // Clear if no quotes
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
