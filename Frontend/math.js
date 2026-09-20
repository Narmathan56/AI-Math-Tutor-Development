// =========================
// PAGE TOGGLE
// =========================
function openWhiteboard() {
    document.getElementById("chatPage").classList.remove("active");
    document.getElementById("canvasPage").classList.add("active");
}

function openChat() {
    document.getElementById("canvasPage").classList.remove("active");
    document.getElementById("chatPage").classList.add("active");
}



// =========================
// GLOBAL STATE
// =========================
let canvas = null;
let ctx = null;
let drawing = false;
let animationVersion = 0;
let pendingAnimation = null;
let tutorRequestVersion = 0;

// streaming buffer
let liveText = "";

// =========================
// INIT CANVAS
// =========================
window.addEventListener("DOMContentLoaded", () => {
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
});


function cleanExpression(expr) {
    return String(expr)
        .replace(/\\text\{([^}]*)\}/g, "$1")
        .replace(/\\pm/g, "±")
        .replace(/\\sqrt\{([^}]*)\}/g, "√($1)")
        .replace(/\\/g, "");
}

// =========================
// DRAW FUNCTIONS
// =========================
function startDraw(e) {
    if (!ctx || pendingAnimation) return;

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
    cancelWhiteboardAnimation();
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

    const requestVersion = ++tutorRequestVersion;
    clearCanvas();
    liveText = "";
    replyText.innerHTML = "";
    container.classList.remove("hidden");

    try {
        const response = await fetch("http://127.0.0.1:8000/solve_math_stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        let buffer = "";

        while (true) {
            const { value, done } = await reader.read();
            if (requestVersion !== tutorRequestVersion) {
                await reader.cancel();
                return;
            }
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // SSE messages are separated by \n\n
            let parts = buffer.split("\n\n");
            buffer = parts.pop();

            for (let part of parts) {

                if (!part.startsWith("data:")) continue;

                const jsonStr = part.replace("data:", "").trim();

                try {
                    const chunk = JSON.parse(jsonStr);

                    // =========================
                    // STREAM TOKEN (TEXT)
                    // =========================
                    if (chunk.type === "token") {

                        liveText += chunk.text;

                        replyText.innerHTML = convertToLatex(liveText);

                        if (ctx) {
                            ctx.clearRect(0, 0, canvas.width, canvas.height);
                            ctx.font = "20px Arial";
                            ctx.fillText(liveText, 20, 50);
                        }
                    }

                    // =========================
                    // FINAL RESULT
                    // =========================
                    if (chunk.type === "done") {

    // parse JSON safely
                        let data = null;

                        try {
        data = typeof chunk.full === "string"
            ? JSON.parse(chunk.full)
            : chunk.full;
    } catch (e) {
        console.error("JSON parse failed", e);
        return;
    }

    // extract clean answer
    const answer = data.final_answer;

    // UI display (clean)
    replyText.innerHTML += `<br><b>Final Answer:</b> ${answer}`;

    // canvas display (clean)
 
    openWhiteboard();
    await drawSolution(data.steps, answer);
}

                } catch (e) {
                    console.error("Stream parse error:", e, jsonStr);
                }
            }
        }

    } catch (err) {
        if (requestVersion !== tutorRequestVersion) return;
        console.error(err);
        replyText.innerHTML = "Backend streaming error";
    }
}

function drawStepArrow(x, y) {
    ctx.beginPath();

    // shaft
    ctx.moveTo(x, y);
    ctx.lineTo(x, y + 25);
    ctx.stroke();

    // arrow head
    ctx.beginPath();
    ctx.moveTo(x - 6, y + 18);
    ctx.lineTo(x, y + 25);
    ctx.lineTo(x + 6, y + 18);
    ctx.stroke();
}


function cancelWhiteboardAnimation() {
    animationVersion++;
    drawing = false;
    if (pendingAnimation) {
        cancelAnimationFrame(pendingAnimation.id);
        const finish = pendingAnimation.finish;
        pendingAnimation = null;
        finish(false);
    }
}

// Resolve false when cancelled so an awaiting drawing loop can stop too.
function animateUnderline(x, y, width, color = "#2563eb", version = animationVersion) {
    return new Promise((resolve) => {
        if (version !== animationVersion || !ctx) {
            resolve(false);
            return;
        }

        const duration = 600;
        let startTime;
        let previousX = x;
        const animation = { id: null, finish: resolve };
        pendingAnimation = animation;

        function frame(time) {
            if (version !== animationVersion) {
                if (pendingAnimation === animation) pendingAnimation = null;
                resolve(false);
                return;
            }
            if (startTime === undefined) startTime = time;
            const progress = Math.min((time - startTime) / duration, 1);
            const nextX = x + width * progress;

            ctx.save();
            ctx.strokeStyle = color;
            ctx.lineWidth = 3;
            ctx.lineCap = "round";
            ctx.beginPath();
            ctx.moveTo(previousX, y);
            ctx.lineTo(nextX, y);
            ctx.stroke();
            ctx.restore();
            previousX = nextX;

            if (progress < 1) {
                animation.id = requestAnimationFrame(frame);
            } else {
                pendingAnimation = null;
                resolve(true);
            }
        }

        animation.id = requestAnimationFrame(frame);
    });
}

// Measure first, then draw the same lines so highlights match wrapped text.
function getWhiteboardLines(text, maxWidth) {
    const lines = [];
    for (const paragraph of String(text).split("\n")) {
        let line = "";
        for (const word of paragraph.split(/\s+/).filter(Boolean)) {
            const candidate = line ? line + " " + word : word;
            if (line && ctx.measureText(candidate).width > maxWidth) {
                lines.push(line);
                line = "";
            }
            // Split oversized expressions rather than clipping them at the edge.
            for (const character of (line ? " " : "") + word) {
                if (line && ctx.measureText(line + character).width > maxWidth) {
                    lines.push(line);
                    line = "";
                }
                line += character;
            }
        }
        lines.push(line);
    }
    return lines;
}

async function drawSolution(steps, answer) {
    if (!canvas || !ctx) return;
    clearCanvas();
    const version = animationVersion;
    const startX = 40;
    const lineHeight = 34;
    const maxWidth = canvas.width - 80;
    const stepFont = "20px Arial";
    const answerFont = "bold 22px Arial";

    ctx.font = stepFont;
    const layout = (Array.isArray(steps) ? steps : []).map((step) => ({
        lines: getWhiteboardLines(
            cleanExpression(step.expression || step.text || ""), maxWidth
        ),
        color: step.emphasis === "key" ? "#b45309" : "#2563eb"
    }));
    ctx.font = answerFont;
    const answerLines = getWhiteboardLines(cleanExpression(answer ?? ""), maxWidth);
    const requiredHeight = 50
        + layout.reduce((height, step) => height + step.lines.length * lineHeight + 60, 0)
        + 40 + answerLines.length * lineHeight + 40;

    // Resizing clears the canvas and resets all context styles.
    canvas.height = Math.max(500, requiredHeight);
    ctx.font = stepFont;
    ctx.fillStyle = "#172033";
    ctx.strokeStyle = "#64748b";
    ctx.lineWidth = 2;

    const wrapper = document.getElementById("canvasWrapper");
    if (wrapper) wrapper.scrollTop = 0;
    function reveal(y) {
        if (!wrapper || !canvas.clientHeight) return;
        const scale = canvas.clientHeight / canvas.height;
        const bottom = canvas.offsetTop - wrapper.offsetTop + (y + 24) * scale;
        if (bottom > wrapper.scrollTop + wrapper.clientHeight) {
            wrapper.scrollTop = bottom - wrapper.clientHeight + 24;
        }
    }

    let y = 50;
    for (let index = 0; index < layout.length; index++) {
        if (version !== animationVersion) return;
        const step = layout[index];
        ctx.font = stepFont;
        const firstY = y;
        for (const line of step.lines) {
            ctx.fillText(line, startX, y);
            y += lineHeight;
        }
        reveal(y);
        for (let lineIndex = 0; lineIndex < step.lines.length; lineIndex++) {
            const finished = await animateUnderline(
                startX, firstY + lineIndex * lineHeight + 8,
                ctx.measureText(step.lines[lineIndex]).width,
                step.color, version
            );
            if (!finished || version !== animationVersion) return;
        }

        if (index < layout.length - 1) drawStepArrow(startX + 20, y + 5);
        y += 60;
    }

    if (version !== animationVersion) return;
    ctx.font = answerFont;
    ctx.fillText("Answer:", startX, y);
    y += 40;
    for (const line of answerLines) {
        const width = ctx.measureText(line).width;
        // Paint the background first, then the readable answer above it.
        ctx.fillStyle = "#dcfce7";
        ctx.fillRect(startX - 8, y - 25, width + 16, lineHeight);
        ctx.fillStyle = "#166534";
        ctx.fillText(line, startX, y);
        reveal(y);
        const finished = await animateUnderline(startX, y + 8, width, "#16a34a", version);
        if (!finished || version !== animationVersion) return;
        y += lineHeight;
    }
    ctx.fillStyle = "#172033";
}