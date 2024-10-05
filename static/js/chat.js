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

async function executeQuery(query, dataset) {
    try {
        const response = await fetch('/api/query_dataset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, dataset }),
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'An error occurred while executing the query');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error executing query:', error);
        throw error;
    }
}

function createQueryResultCard(queryResult) {
    const card = document.createElement('div');
    card.className = 'bg-white shadow-md rounded-lg p-4 my-2';
    card.innerHTML = `
        <h3 class="font-bold text-lg mb-2">Query Result</h3>
        <div class="overflow-x-auto">
            <table class="min-w-full bg-white">
                <thead class="bg-gray-100">
                    <tr>${Object.keys(queryResult[0]).map(key => `<th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">${key}</th>`).join('')}</tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                    ${queryResult.map(row => `
                        <tr>
                            ${Object.values(row).map(value => `<td class="px-4 py-2 whitespace-nowrap">${value}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    return card;
}

async function processDataQueryJson(queryJson, chatMessages) {
    try {
        const query = JSON.parse(queryJson);
        const dataset = query.dataset;
        
        if (!dataset || !dataset.includes('/')) {
            throw new Error("Invalid dataset format. Expected 'organization/dataset'");
        }
        
        const queryResult = await executeQuery(query, dataset);
        
        if (Array.isArray(queryResult) && queryResult.length > 0) {
            const resultCard = createQueryResultCard(queryResult);
            chatMessages.appendChild(resultCard);
        } else {
            const noResultElement = document.createElement('div');
            noResultElement.className = 'p-3 rounded-lg bg-yellow-100 text-yellow-800 my-2';
            noResultElement.textContent = 'The query returned no results.';
            chatMessages.appendChild(noResultElement);
        }
        
        // Generate LLM response for the query result
        const llmResponse = await generateLLMResponseForQueryResult(queryResult);
        
        const llmResponseElement = document.createElement('div');
        llmResponseElement.className = 'p-3 rounded-lg bg-gray-100 text-gray-800 my-2';
        llmResponseElement.textContent = llmResponse;
        chatMessages.appendChild(llmResponseElement);
        
    } catch (error) {
        console.error('Error processing data-query-json:', error);
        const errorElement = document.createElement('div');
        errorElement.className = 'p-3 rounded-lg bg-red-100 text-red-800 my-2';
        errorElement.textContent = `Error executing query: ${error.message}`;
        chatMessages.appendChild(errorElement);
    }
}

async function generateLLMResponseForQueryResult(queryResult) {
    // This function should call the backend to generate an LLM response for the query result
    // For now, we'll just return a placeholder message
    return "Here's an analysis of the query result: [Placeholder for LLM-generated analysis]";
}

function processLLMResponse(response, chatMessagesElement) {
    const dataQueryJsonRegex = /```data-query-json\s*([\s\S]*?)```/g;
    let match;
    let lastIndex = 0;
    let processedResponse = '';

    while ((match = dataQueryJsonRegex.exec(response)) !== null) {
        processedResponse += response.slice(lastIndex, match.index);
        const queryJson = match[1];
        processDataQueryJson(queryJson, chatMessagesElement);
        lastIndex = dataQueryJsonRegex.lastIndex;
    }

    processedResponse += response.slice(lastIndex);
    return processedResponse;
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

        // Parse retrieved information
        if (data.retrieved_information) {
            console.log("Retrieved information:", data.retrieved_information);
            try {
                const parsedInfo = JSON.parse(data.retrieved_information);
                console.log("Parsed information:", parsedInfo);
                
                // Update datasets and datacards
                datasets = parsedInfo.datasets || [];
                datacards = parsedInfo.datacards || [];
                
                console.log("Updated datasets:", datasets);
                console.log("Updated datacards:", datacards);
                
                // Update sidebar with new information
                updateSidebar();
            } catch (error) {
                console.error("Error parsing retrieved information:", error);
            }
        }

        // Parse suggested query
        let suggestedQuery = null;
        if (data.suggested_query) {
            try {
                suggestedQuery = JSON.parse(data.suggested_query);
                console.log("Suggested query:", suggestedQuery);
            } catch (error) {
                console.error("Error parsing suggested query:", error);
            }
        }

        // Process LLM response
        const processedResponse = processLLMResponse(data.message, chatMessages);

        // Add LLM response to chat
        const llmMessageElement = document.createElement('div');
        llmMessageElement.className = 'p-3 rounded-lg bg-gray-100 text-gray-800 my-2';
        llmMessageElement.innerHTML = processedResponse;
        chatMessages.appendChild(llmMessageElement);

        // If there's a valid suggested query, create and append a command card for it
        if (suggestedQuery && suggestedQuery.description && suggestedQuery.dataset) {
            const queryCard = createCommandCard('query_dataset', suggestedQuery.description, suggestedQuery.dataset);
            chatMessages.appendChild(queryCard);
        }

        // Update chat history
        chatHistory.push({ 
            role: 'assistant', 
            content: data.message,
            retrieved_information: data.retrieved_information,
            suggested_query: data.suggested_query
        });

    } catch (error) {
        console.error('Error:', error);
        const errorElement = document.createElement('div');
        errorElement.className = 'p-3 rounded-lg bg-red-100 text-red-800 my-2';
        errorElement.textContent = `Error: ${error.message}`;
        chatMessages.appendChild(errorElement);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
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
            <ul class="space-y-2">
                ${datasets.map(dataset => `
                    <li class="dataset-item">
                        <div class="flex items-center">
                            <i class="fas fa-database text-blue-500 mr-2"></i>
                            <div>
                                <div class="font-semibold">${dataset.description}</div>
                                <div class="text-sm text-gray-500">${dataset.organization}/${dataset.dataset_slug}</div>
                            </div>
                        </div>
                        <div class="dataset-details hidden mt-2 text-sm">
                            <div><strong>Measures:</strong> ${dataset.measures.join(', ')}</div>
                            <div><strong>Dimensions:</strong> ${dataset.dimensions.join(', ')}</div>
                        </div>
                    </li>
                `).join('')}
            </ul>
        </div>
        <div>
            <h2 class="font-bold text-lg mb-2">Datacards</h2>
            <ul class="space-y-2">
                ${datacards.map(datacard => `
                    <li class="datacard-item">
                        <div class="flex items-center">
                            <i class="fas fa-chart-bar text-green-500 mr-2"></i>
                            <div>
                                <div class="font-semibold">${datacard.name}</div>
                                <div class="text-sm text-gray-500">${datacard.organization}/${datacard.datacard_slug}</div>
                            </div>
                        </div>
                    </li>
                `).join('')}
            </ul>
        </div>
    `;

    // Add hover effect for dataset items
    const datasetItems = sidebar.querySelectorAll('.dataset-item');
    datasetItems.forEach(item => {
        const details = item.querySelector('.dataset-details');
        item.addEventListener('mouseenter', () => details.classList.remove('hidden'));
        item.addEventListener('mouseleave', () => details.classList.add('hidden'));
    });

    console.log("Sidebar updated");
}

function addMessageToChat(content, isUser = false) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) {
        console.error("Chat messages container not found");
        return;
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.querySelector('form');
    const chatInput = document.querySelector('input[name="message"]');
    const chatMessages = document.getElementById('chat-messages');

    if (!chatForm || !chatInput || !chatMessages) {
        console.error("Required elements not found");
        return;
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userMessage = chatInput.value.trim();
        if (!userMessage) return;

        // Add user message to chat
        addMessageToChat(userMessage, true);

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