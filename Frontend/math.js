function convertToLatex(text) {
    // Convert x2 → x^2, x10 → x^10
    return text.replace(/([a-zA-Z])(\d+)/g, '$1^{$2}');
}

function renderMath() {
    renderMathInElement(document.getElementById("replyText"), {
        delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false }
        ]
    });
}

async function askTutor() {
    const question = document.getElementById('mathQuestion').value;
    const responseContainer = document.getElementById('responseContainer');
    const replyText = document.getElementById('replyText');

    if (!question) {
        alert("Please type a question first!");
        return;
    }

    replyText.innerHTML = "Thinking...";
    responseContainer.classList.remove('hidden');

    try {
        const response = await fetch('http://127.0.0.1:8000/solve_math', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        let output = "";

        if (data.type === "solution") {

            const sol = data.data || {};

            output += "<b>Steps:</b><br>";

            if (Array.isArray(sol.steps)) {
                sol.steps.forEach((step, index) => {

                    let stepContent = typeof step === "object"
                        ? step.text || step.explanation || step.calculation
                        : step;

                    stepContent = convertToLatex(stepContent);

                    output += `${index + 1}. $$${stepContent}$$ <br>`;
                });
            }

            if (sol.final_answer !== undefined) {
                let finalAns = convertToLatex(sol.final_answer);
                output += `<br><b>Final Answer:</b> $$${finalAns}$$`;
            }

            output += `<br><br>🧠 Model: ${data.model_used || "unknown"}`;
        }

        else if (data.type === "chat") {
            let responseText = convertToLatex(data.data?.response || "");
            output = `$$${responseText}$$`;
        }

        else if (data.type === "error") {
            output = `⚠️ ${data.data?.reason}`;
        }

        else {
            output = "Unexpected response format.";
        }

        replyText.innerHTML = output;

        // 🔥 IMPORTANT: render math AFTER inserting HTML
        renderMath();

    } catch (error) {
        replyText.innerHTML = "🚫 Backend connection error";
        console.error(error);
    }
}