# TN Board MCQ Tester

A modern, minimal MCQ testing web app for Tamil Nadu State Board students (+1 and +2). This app is built purely with frontend technologies (HTML, CSS, JavaScript) and is designed for fast performance, ease of use, and deployment on static hosting platforms like GitHub Pages or Cloudflare Pages.

## Features

-   **Standard Selection:** Choose between +1 and +2 standards.
-   **Subject Selection:** Pick from available subjects (e.g., Physics, Chemistry).
-   **Lesson Selection:** Choose a specific lesson from the selected subject.
-   **Mixed Questions Mode:** Get random MCQs from all lessons in the selected subject.
-   **Scrollable Quiz Interface:** All questions are displayed on a single, scrollable page, similar to Google Forms.
-   **Question Format:** Each question includes text and 4 radio button options. Image support is included if present in the data.
-   **Countdown Timer:** Calculated as 4 minutes × number of questions. The test auto-submits when time runs out.
-   **Instant Results:** View score, percentage, and a message upon submission.
-   **Detailed Review:** Incorrect answers are displayed with the question, your selected answer, and the correct answer.
-   **Retake & Return:** Options to retake the same quiz or return to the homepage.
-   **Animations:** Soft animations like a slide-in result panel and confetti for high scores.
-   **Mobile-Friendly:** Fully responsive design.
-   **Dark Mode:** Toggle for light/dark theme preference (persists via local storage).
-   **Static & Deployable:** No backend required, runs entirely client-side.

## How to Use

1.  **Open `index.html`:** Launch the `index.html` file in your web browser.
2.  **Homepage Selection:**
    *   Select your **Standard** (+1 or +2).
    *   Select your **Subject**.
    *   Choose a specific **Lesson** OR check the **"Mixed Questions"** box to get questions from all lessons in that subject.
    *   Click **"Start Quiz"**.
3.  **Quiz Interface:**
    *   The timer will start at the top right.
    *   Scroll through the questions and select your answer for each.
    *   Click **"Submit Test"** at the bottom when you're done, or the test will auto-submit when the timer ends.
4.  **Result Page:**
    *   View your score, percentage, and feedback.
    *   Review any incorrect answers.
    *   Choose to **"Retake Test"** or **"Return to Home"**.

## Data Format

Quiz questions are stored in static JSON files located in the `/data` directory. The structure is as follows:

`/data/{standard}/{subject}/{lessonName}.json`

For example:
-   `/data/+1/physics/lesson1.json`
-   `/data/+2/chemistry/lesson1.json`

Each JSON file should be an array of question objects:

```json
[
  {
    "question": "What is the SI unit of pressure?",
    "options": ["Newton", "Pascal", "Joule", "Watt"],
    "answer": "Pascal",
    "image": "optional_url_to_image.png" // Optional: null or omit if no image
  },
  {
    "question": "Another question...",
    "options": ["A", "B", "C", "D"],
    "answer": "C",
    "image": null
  }
]
```

**Adding New Subjects/Lessons:**

1.  Create the necessary directory structure under `/data`. For example, for a new subject "Botany" in "+1": `/data/+1/botany/`.
2.  Add your lesson JSON files (e.g., `lesson1.json`, `lesson2.json`) into this new directory.
3.  Update the `availableData` object in `js/app.js` to include the new subject and its lessons:

    ```javascript
    const availableData = {
        "+1": {
            "Physics": ["lesson1", "lesson2"],
            "Chemistry": ["lesson1"],
            "Botany": ["lesson1", "lesson2"] // Added new subject
        },
        "+2": {
            // ... other subjects
        }
    };
    ```
    *Note: The subject name in `availableData` (e.g., "Physics") is used for display, while the directory and option values use its lowercase version (e.g., "physics"). Lesson file names (e.g., "lesson1") are used directly.*

## Deployment

This web app is fully static and can be deployed on any static site hosting service.

**GitHub Pages:**
1.  Push the entire project (index.html, css/, js/, data/ folders) to a GitHub repository.
2.  Go to your repository's **Settings** > **Pages**.
3.  Under "Build and deployment", select **"Deploy from a branch"** as the source.
4.  Choose the branch (e.g., `main` or `master`) and the `/ (root)` folder.
5.  Click **Save**. Your site should be live shortly at `your-username.github.io/repository-name/`.

**Cloudflare Pages:**
1.  Push your project to a GitHub or GitLab repository.
2.  Log in to your Cloudflare dashboard and go to **Workers & Pages**.
3.  Click **Create application** > **Pages** > **Connect to Git**.
4.  Select your repository.
5.  In the "Set up builds and deployments" section, the framework preset can be "None". No build command or output directory is typically needed for a plain HTML/CSS/JS project.
6.  Click **Save and Deploy**.

## Technologies Used

-   HTML5
-   CSS3 (with Tailwind CSS for styling)
-   JavaScript (Vanilla)
-   [canvas-confetti](https://github.com/catdad/canvas-confetti) for the confetti animation.

## Contributing

Feel free to fork this repository and submit pull requests for improvements or new features. If you encounter any bugs, please open an issue.
