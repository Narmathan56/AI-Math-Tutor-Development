// =========================
// GLOBAL STATE
// =========================
let canvas = null;
let ctx = null;
let drawing = false;

// =========================
// INIT CANVAS (SAFE)
// =========================
window.onload = () => {
    canvas = document.getElementById("board");

    if (!canvas) {
        console.error("Canvas not found!");
        return;
    }

    ctx = canvas.getContext("2d");

    // Mouse events
    canvas.addEventListener("mousedown", startDraw);
    canvas.addEventListener("mousemove", draw);
    canvas.addEventListener("mouseup", stopDraw);
    canvas.addEventListener("mouseleave", stopDraw);
};

// =========================
// DRAW FUNCTIONS
// =========================
function startDraw(e) {
    if (!ctx) return;

    drawing = true;
    ctx.beginPath();
    ctx.moveTo(e.offsetX, e.offsetY);
}

function draw(e) {
    if (!drawing || !ctx) return;

    ctx.lineWidth = 2;
    ctx.lineCap = "round";

    ctx.lineTo(e.offsetX, e.offsetY);
    ctx.stroke();
}

function stopDraw() {
    drawing = false;
}

// =========================
// CLEAR CANVAS
// =========================
function clearCanvas() {
    if (!ctx || !canvas) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

// =========================
// LATEX HELPER
// =========================
function convertToLatex(text) {
    if (!text) return "";
    return text.replace(/([a-zA-Z])(\d+)/g, "$1^{$2}");
}

// =========================
// MATH RENDER
// =========================
function renderMath() {
    renderMathInElement(document.getElementById("replyText"), {
        delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false }
        ]
    });
}

// =========================
// MAIN API CALL
// =========================
async function askTutor() {
    const question = document.getElementById("mathQuestion").value;
    const replyText = document.getElementById("replyText");
    const responseContainer = document.getElementById("responseContainer");

    if (!question) {
        alert("Please type a question first!");
        return;
    }

    replyText.innerHTML = "Thinking...";
    responseContainer.classList.remove("hidden");

    try {
        const response = await fetch("http://127.0.0.1:8000/solve_math", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        let output = "";

        // =========================
        // SOLUTION TYPE
        // =========================
        if (data.type === "solution") {
            const sol = data.data || {};

            output += "<b>Steps:</b><br>";

            if (Array.isArray(sol.steps)) {
                sol.steps.forEach((step, index) => {
                    let stepContent =
                        typeof step === "object"
                            ? step.text || step.expression || ""
                            : step;

                    stepContent = convertToLatex(stepContent);

                    output += `${index + 1}. $$${stepContent}$$ <br>`;
                });
            }

            if (sol.final_answer !== undefined) {
                output += `<br><b>Final Answer:</b> $$${convertToLatex(sol.final_answer)}$$`;
            }

            output += `<br><br>🧠 Model: ${data.model_used || "unknown"}`;

            replyText.innerHTML = output;
            renderMath();

            // 👉 CONNECT TO CANVAS
            drawSolution(sol.steps || [], sol.final_answer || []);
        }

        // =========================
        // CHAT TYPE
        // =========================
        else if (data.type === "chat") {
            const msg = data.data?.response || "";

            output = convertToLatex(msg);
            replyText.innerHTML = `$$${output}$$`;

            renderMath();

            // 👉 SHOW ON CANVAS ALSO
            clearCanvas();
            if (ctx) {
                ctx.font = "20px Arial";
                ctx.fillText(msg, 20, 50);
            }
        }

        // =========================
        // ERROR TYPE
        // =========================
        else if (data.type === "error") {
            replyText.innerHTML = `⚠️ ${data.data?.reason || "Error"}`;
        }

        else {
            replyText.innerHTML = "Unexpected response format";
        }

    } catch (err) {
        console.error(err);
        replyText.innerHTML = "🚫 Backend connection error";
    }
}

// =========================
// DRAW SOLUTION ON CANVAS
// =========================
async function drawSolution(steps, answer) {
    if (!ctx) return;

    clearCanvas();

    ctx.font = "18px Arial";
    ctx.fillStyle = "black";

    let y = 40;

    for (const step of steps || []) {
        const text = step.expression || step.text || "";

        ctx.fillText(text, 20, y);
        y += 40;

        await new Promise(r => setTimeout(r, 500));
    }

    ctx.fillText("Answer: " + answer, 20, y);
}