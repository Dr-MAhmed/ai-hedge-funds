const { init } = require("@heyputer/puter.js/src/init.cjs");

let puterInstance = null;

function getPuter(authToken) {
    if (!puterInstance) {
        puterInstance = init(authToken);
    }
    return puterInstance;
}

async function chat(messages, model, authToken) {
    const puter = getPuter(authToken);

    const response = await puter.ai.chat(messages, {
        model: model,
        temperature: 0.1,
        max_tokens: 512,
    });

    return {
        content: response.message.content,
        model: model,
    };
}

async function main() {
    const args = process.argv.slice(2);
    const authToken = args[0];
    const model = args[1] || "deepseek/deepseek-chat-v3.1";

    let inputData = "";
    process.stdin.setEncoding("utf8");
    for await (const chunk of process.stdin) {
        inputData += chunk;
    }

    try {
        const request = JSON.parse(inputData);
        const messages = request.messages || [];

        const result = await chat(messages, model, authToken);
        process.stdout.write(JSON.stringify(result));
    } catch (error) {
        process.stderr.write(JSON.stringify({ error: error.message }));
        process.exit(1);
    }
}

main();
