import { renderDatacard } from './datacard_renderer.js';

const commandHandlers = {
    search_dataset: async (query) => {
        const response = await fetch(`/api/search_dataset?query=${encodeURIComponent(query)}`);
        return await response.json();
    },
    search_datacard: async (query) => {
        const response = await fetch(`/api/search_datacard?query=${encodeURIComponent(query)}`);
        return await response.json();
    },
    query_dataset: async (query, dataset) => {
        const response = await fetch('/api/query_dataset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, dataset }),
        });
        return await response.json();
    },
};

function createCommandCard(command, query, dataset = null) {
    const card = document.createElement('div');
    card.className = 'bg-white shadow-md rounded-lg p-4 my-2';
    card.innerHTML = `
        <h3 class="font-bold text-lg mb-2">${command}</h3>
        <p>Query: ${query}</p>
        ${dataset ? `<p>Dataset: ${dataset}</p>` : ''}
        <button class="bg-blue-500 text-white px-4 py-2 rounded mt-2 execute-command">Execute</button>
        <div class="result mt-2 hidden"></div>
    `;

    const executeButton = card.querySelector('.execute-command');
    const resultDiv = card.querySelector('.result');

    executeButton.addEventListener('click', async () => {
        executeButton.disabled = true;
        executeButton.textContent = 'Executing...';
        try {
            const result = await commandHandlers[command](query, dataset);
            resultDiv.textContent = JSON.stringify(result, null, 2);
            resultDiv.classList.remove('hidden');
            card.dispatchEvent(new CustomEvent('command-executed', { detail: result }));
        } catch (error) {
            resultDiv.textContent = `Error: ${error.message}`;
            resultDiv.classList.remove('hidden');
        } finally {
            executeButton.disabled = false;
            executeButton.textContent = 'Execute';
        }
    });

    return card;
}

function processLLMResponse(response, chatMessagesElement, onCommandExecuted) {
    const commandRegex = /<\$(\w+)\s+([^>]+?)\s*\/?>/g;  // Modified regex to match both with and without closing '/'
    let match;
    let lastIndex = 0;
    let processedResponse = '';
    const commandCards = [];

    while ((match = commandRegex.exec(response)) !== null) {
        processedResponse += response.slice(lastIndex, match.index);
        const [fullMatch, command, attributesString] = match;
        
        const attributes = {};
        attributesString.replace(/(\w+)="([^"]*)"/g, (_, key, value) => {
            attributes[key] = value;
            return '';
        });

        if (command in commandHandlers) {
            const card = createCommandCard(command, attributes.query, attributes.from);
            commandCards.push(card);
            card.addEventListener('command-executed', (event) => onCommandExecuted(command, event.detail));
        } else {
            processedResponse += fullMatch;
        }

        lastIndex = commandRegex.lastIndex;
    }

    processedResponse += response.slice(lastIndex);

    return { processedResponse, commandCards };
}

let chatHistory = [];

async function sendMessage(message, chatMessages, isCommandResult = false) {
    try {
        const formData = new FormData();
        formData.append('message', message);
        formData.append('chat_history', JSON.stringify(chatHistory));

        const response = await fetch('/api/chat', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (response.status !== 200) {
            throw new Error(data.error || 'An error occurred');
        }

        const { processedResponse, commandCards } = processLLMResponse(data.message, chatMessages, async (command, result) => {
            await sendMessage(JSON.stringify({ command, result }), chatMessages, true);
        });

        // Add processed LLM response to chat
        if (processedResponse.trim()) {
            const llmMessageElement = document.createElement('div');
            llmMessageElement.className = 'p-3 rounded-lg bg-gray-100 text-gray-800 my-2';
            llmMessageElement.textContent = processedResponse;
            chatMessages.appendChild(llmMessageElement);

            // Update chat history
            if (chatHistory.length > 0 && chatHistory[chatHistory.length - 1].role === 'assistant') {
                chatHistory[chatHistory.length - 1].content += '\n' + processedResponse;
            } else {
                chatHistory.push({ role: 'assistant', content: processedResponse });
            }
        }

        // Add command cards
        commandCards.forEach(card => chatMessages.appendChild(card));

        // If there are command cards, wait for all of them to be executed
        if (commandCards.length > 0) {
            await Promise.all(commandCards.map(card => {
                return new Promise(resolve => {
                    card.addEventListener('command-executed', resolve, { once: true });
                });
            }));
        }

    } catch (error) {
        console.error('Error:', error);
        const errorElement = document.createElement('div');
        errorElement.className = 'p-3 rounded-lg bg-red-100 text-red-800 my-2';
        errorElement.textContent = `Error: ${error.message}`;
        chatMessages.appendChild(errorElement);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.querySelector('form');
    const chatInput = document.querySelector('input[name="message"]');
    const chatMessages = document.getElementById('chat-messages');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userMessage = chatInput.value.trim();
        if (!userMessage) return;

        // Add user message to chat
        const userMessageElement = document.createElement('div');
        userMessageElement.className = 'p-3 rounded-lg bg-blue-100 text-blue-800 ml-auto my-2';
        userMessageElement.textContent = userMessage;
        chatMessages.appendChild(userMessageElement);

        // Update chat history
        if (chatHistory.length > 0 && chatHistory[chatHistory.length - 1].role === 'user') {
            chatHistory[chatHistory.length - 1].content += '\n' + userMessage;
        } else {
            chatHistory.push({ role: 'user', content: userMessage });
        }

        chatInput.value = '';

        await sendMessage(userMessage, chatMessages);
    });
});