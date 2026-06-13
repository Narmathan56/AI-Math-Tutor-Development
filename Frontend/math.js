// =========================
// GLOBAL STATE
// =========================
let canvas = null;
let ctx = null;
let drawing = false;

// streaming buffer
let liveText = "";

// =========================
// INIT CANVAS
// =========================
window.onload = () => {
    canvas = document.getElementById("board");

    if (!canvas) {
        console.error("Canvas not found!");
        return;
    }

    ctx = canvas.getContext("2d");

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
// SAFE TEXT CONVERTER
// =========================
function convertToLatex(text) {
    if (text === null || text === undefined) return "";
    text = String(text);

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
// STREAMING RENDER (CHAT + CANVAS SYNC)
// =========================
function updateLiveUI(chunk) {
    const replyText = document.getElementById("replyText");

    liveText += chunk;

    // show chat live
    replyText.innerHTML = convertToLatex(liveText);

    // optional: live canvas update
    if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.font = "20px Arial";
        ctx.fillText(liveText, 20, 50);
    }
}

// =========================
// MAIN STREAMING CALL
// =========================
async function askTutor() {

    const question = document.getElementById("mathQuestion").value;
    const replyText = document.getElementById("replyText");
    const container = document.getElementById("responseContainer");

    if (!question) return;

    liveText = "";
    replyText.innerHTML = "Thinking...";
    container.classList.remove("hidden");

    try {
        const response = await fetch("http://127.0.0.1:8000/solve_math", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        console.log("RESPONSE:", data);

        if (data.type === "solution") {

            const sol = data.data;

            // TEXT
            let output = "<b>Steps:</b><br>";

            for (const step of sol.steps || []) {
                output += `• ${step.text || step.expression}<br>`;
            }

            output += `<br><b>Answer:</b> ${sol.final_answer}`;

            replyText.innerHTML = output;

            // CANVAS
            drawSolution(sol.steps, sol.final_answer);
        }

        else if (data.type === "chat") {
            replyText.innerHTML = data.data.response;
            ctx.fillText(data.data.response, 20, 50);
        }

    } catch (err) {
        console.error(err);
        replyText.innerHTML = "Backend error";
    }
}

// =========================
// FINAL CANVAS DRAW
// =========================
function drawSolution(steps, answer) {

    if (!ctx) return;

    clearCanvas();

    ctx.font = "18px Arial";
    ctx.fillStyle = "black";

    let y = 40;

    for (const step of steps || []) {
        const text = step.expression || step.text || "";
        ctx.fillText(text, 20, y);
        y += 40;
    }

    if (answer) {
        ctx.fillText("Answer: " + answer, 20, y);
    }
}