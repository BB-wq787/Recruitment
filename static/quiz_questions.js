// DKSH Stamp Quiz Questions Database
// Add new questions here in the following format:
// {
//     question: "Your question here?",
//     answer: "correct_answer"
// }

const quizQuestions = [
    {
        question: "How many fields does DKSH provide services in total?",
        answer: "four"
    },
    {
        question: "In which year was DKSH founded?",
        answer: "1865"
    },
    {
        question: "In what fields does MTDC mainly serve?",
        answer: "healthcare"
    }
];

// You can add more questions below:
// {
//     question: "New question?",
//     answer: "new_answer"
// }

// Export for potential use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = quizQuestions;
}
