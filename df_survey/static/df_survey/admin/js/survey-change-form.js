
function setAddQuestionEventListener() {
    function setNextSequence() {
        let maxOrder = 0;
        const inputs = [...document.querySelectorAll('#question_set-group .field-sequence input')]

        inputs.forEach((input, idx) => {
            if (idx === inputs.length - 1) {
                input.value = maxOrder + 1;
            } else {
                maxOrder = Math.max(maxOrder, parseInt(input.value) || maxOrder);
            }
        })
    }

    const addButton = document.querySelector('#question_set-group .add-row a');
    if (!addButton) {
        setTimeout(setAddQuestionEventListener, 100);
        return;
    }

    setNextSequence()
    addButton.addEventListener('click', () => {
        setTimeout(setNextSequence, 0);
    });
}
setAddQuestionEventListener()
