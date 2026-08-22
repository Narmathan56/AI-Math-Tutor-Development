
function renderVisual(instructions) {
    instructions.forEach(instruction => {

        switch (instruction.type) {

            case "circle":
                drawCircle(
                    instruction.x,
                    instruction.y,
                    instruction.radius
                );
                break;

            case "rectangle":
                drawRectangle(
                    instruction.x,
                    instruction.y,
                    instruction.width,
                    instruction.height
                );
                break;
        }
    });
}