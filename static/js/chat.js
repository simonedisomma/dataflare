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
let datasets = [];
let datacards = [];

// Add this function definition
function onCommandExecuted(command, result) {
    console.log(`Command ${command} executed with result:`, result);
    // You can add more logic here to handle the command execution result
}

async function sendMessage(message, chatMessages) {
    try {
        const formData = new FormData();
        formData.append('message', message);
        formData.append('chat_history', JSON.stringify(chatHistory));

        const response = await fetch('/api/chat', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();
        console.log("Received data from backend:", data);

        if (response.status !== 200) {
            throw new Error(data.error || 'An error occurred');
        }

        // Parse retrieved information from the message text
        const parsedInfo = parseRetrievedInformation(data.message);
        console.log("Parsed information:", parsedInfo);
        
        // Update datasets and datacards
        if (parsedInfo.datasets.length > 0) {
            datasets = [...new Set([...datasets, ...parsedInfo.datasets.map(d => d.name)])];
        }
        if (parsedInfo.datacards.length > 0) {
            datacards = [...new Set([...datacards, ...parsedInfo.datacards.map(d => d.name)])];
        }
        
        console.log("Updated datasets:", datasets);
        console.log("Updated datacards:", datacards);
        
        // Always call updateSidebar, even if no new information was added
        updateSidebar();

        // Process LLM response
        const { processedResponse, commandCards } = processLLMResponse(data.message, chatMessages, onCommandExecuted);

        // Add LLM response to chat
        const llmMessageElement = document.createElement('div');
        llmMessageElement.className = 'p-3 rounded-lg bg-gray-100 text-gray-800 my-2';
        llmMessageElement.innerHTML = processedResponse;
        chatMessages.appendChild(llmMessageElement);

        // Append command cards
        commandCards.forEach(card => chatMessages.appendChild(card));

        // Update chat history
        chatHistory.push({ role: 'assistant', content: data.message });

    } catch (error) {
        console.error('Error:', error);
        const errorElement = document.createElement('div');
        errorElement.className = 'p-3 rounded-lg bg-red-100 text-red-800 my-2';
        errorElement.textContent = `Error: ${error.message}`;
        chatMessages.appendChild(errorElement);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function parseRetrievedInformation(message) {
    const retrievedInfoMatch = message.match(/Retrieved Information:(.+?)(?=AI Response:)/s);
    if (!retrievedInfoMatch) return { datasets: [], datacards: [] };

    const retrievedInfo = retrievedInfoMatch[1];
    const datasetsMatch = retrievedInfo.match(/Datasets:\s*(.+?)(?=\s*Measures:|$)/s);
    const measuresMatch = retrievedInfo.match(/Measures:\s*(.+?)(?=\s*Dimensions:|$)/s);
    const dimensionsMatch = retrievedInfo.match(/Dimensions:\s*(.+?)(?=\s*Datacards:|$)/s);
    const datacardsMatch = retrievedInfo.match(/Datacards:\s*(.+?)(?=\s*$)/s);

    const datasets = datasetsMatch ? [
        {
            name: datasetsMatch[1].trim().replace(/^-\s*/, ''),
            description: "Monthly US unemployment rate",
            measures: measuresMatch ? measuresMatch[1].split(',').map(m => m.trim()) : [],
            dimensions: dimensionsMatch ? dimensionsMatch[1].split(',').map(d => d.trim()) : []
        }
    ] : [];

    const datacards = datacardsMatch ? datacardsMatch[1].split('-').map(d => {
        const [name, description] = d.split(':').map(s => s.trim());
        return { name: name.replace(/^-\s*/, ''), description };
    }).filter(d => d.name && d.name !== "Unnamed datacard") : [];

    return { datasets, datacards };
}

function updateSidebar() {
    console.log("Updating sidebar");
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) {
        console.error("Sidebar element not found");
        return;
    }
    
    sidebar.innerHTML = `
        <div class="mb-6">
            <h2 class="font-bold text-lg mb-2">Datasets</h2>
            <ul class="list-disc pl-5">
                ${datasets.map(dataset => `<li>${dataset}</li>`).join('')}
            </ul>
        </div>
        <div>
            <h2 class="font-bold text-lg mb-2">Datacards</h2>
            <ul class="list-disc pl-5">
                ${datacards.map(datacard => `<li>${datacard}</li>`).join('')}
            </ul>
        </div>
    `;
    console.log("Sidebar updated");
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

    // Initialize sidebar
    updateSidebar();
});