
// --- Application State ---
let categories = [];
let documents = [];
let processedDocuments = [];
let pendingDocuments = []; // Renamed from processingDocuments
let unknownPool = [];

let currentDoc = null;
let selectedCategoryId = null;
let kvData = [];

const userId = 'mock-user-id';
const DOCS_PER_PAGE = 15;
let currentDocumentPage = 1;
let currentPendingPage = 1; // Renamed from currentProcessingPage
let currentUnknownPage = 1;

// --- API Helper ---
const api = {
    async get(endpoint) {
        const response = await fetch(`/api/v1${endpoint}`);
        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
        return response.json();
    },
    async post(endpoint, body = {}) { // Default body to empty object
        const response = await fetch(`/api/v1${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
        return response.json();
    },
    async postFile(endpoint, formData) {
        const response = await fetch(`/api/v1${endpoint}`, {
            method: 'POST',
            body: formData,
        });
        // Handle both OK and Created statuses
        if (![200, 201].includes(response.status)) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.statusText} - ${errorText}`);
        }
        return response.json();
    },
    async delete(endpoint) {
        const response = await fetch(`/api/v1${endpoint}`, {
            method: 'DELETE',
        });
        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
        return response.json();
    }
};

// --- Initialization ---
function showLoading(show) {
    document.getElementById('loadingOverlay').classList.toggle('hidden', !show);
}

async function initializeApp() {
    showLoading(true);
    try {
        const [fetchedCategories, fetchedDocuments] = await Promise.all([
            api.get('/categories'),
            api.get('/documents'),
        ]);

        categories = fetchedCategories;
        documents = fetchedDocuments;

        updateDocumentPools();
        console.log("Data loaded from backend.");

    } catch (error) {
        console.error("Initialization failed:", error);
    } finally {
        showLoading(false);
    }
}

function updateDocumentPools() {
    const activeDocuments = documents.filter(d => d.status !== 'Archived');
    processedDocuments = activeDocuments.filter(d => d.status === 'Processed');
    pendingDocuments = activeDocuments.filter(d => ['Pending', 'Uploaded'].includes(d.status));
    unknownPool = activeDocuments.filter(d => d.status === 'Unknown');

    renderCategoryList();
    renderDocumentLists();

    if (!selectedCategoryId && categories.length > 0) {
        selectCategory(categories[0].id);
    }

    if (currentDoc && currentDoc.status === 'Archived') {
        currentDoc = null;
        switchToView('viewA');
    }

    if (!currentDoc && processedDocuments.length > 0) {
        selectDocument(processedDocuments[0].id);
    } else if (currentDoc) {
        const updatedDoc = documents.find(d => d.id === currentDoc.id);
        if (updatedDoc) {
            currentDoc = updatedDoc;
            kvData = updatedDoc.kv_data || [];
            updateMainViewInfo();
        } else {
            currentDoc = null;
            switchToView('viewA'); 
        }
    }
}

// --- UI Rendering ---
function handleSearch() {
    currentDocumentPage = 1;
    currentPendingPage = 1;
    currentUnknownPage = 1;
    renderDocumentLists();
}

function loadMoreDocuments() {
    const activeTab = getActiveTab();
    if (activeTab === 'pending') {
        currentPendingPage++;
    } else if (activeTab === 'unknown') {
        currentUnknownPage++;
    } else {
        currentDocumentPage++;
    }
    renderDocumentLists();
}

function renderCategoryList() {
    const categoryListEl = document.getElementById('categoryList');
    if (!selectedCategoryId && categories.length > 0) {
        selectedCategoryId = categories[0].id;
    }

    categoryListEl.innerHTML = categories.map(cat => {
        const docCount = processedDocuments.filter(d => d.categoryId === cat.id).length;
        return `
            <div onclick="selectCategory('${cat.id}')" class="p-2 cursor-pointer rounded-lg text-sm transition duration-150 ${selectedCategoryId === cat.id ? 'bg-indigo-100 text-indigo-700 font-semibold' : 'hover:bg-gray-100 text-gray-700'}">
                <i data-lucide="folder" class="w-4 h-4 inline-block mr-2"></i>
                ${cat.name} (${docCount})
            </div>
        `;
    }).join('');

    lucide.createIcons();
}

function selectCategory(categoryId) {
    if (selectedCategoryId !== categoryId) {
        currentDocumentPage = 1;
        selectedCategoryId = categoryId;
        renderCategoryList();
        switchDocumentList('documents');
    }
}

function getActiveTab() {
    if (document.getElementById('tabPending').classList.contains('border-indigo-600')) return 'pending';
    if (document.getElementById('tabUnknown').classList.contains('border-indigo-600')) return 'unknown';
    return 'documents';
}

function renderDocumentLists() {
    const docListEl = document.getElementById('documentList');
    const pendListEl = document.getElementById('pendingList');
    const unknownListEl = document.getElementById('unknownList');
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    const searchTerm = document.getElementById('documentSearch').value.trim().toLowerCase();

    const activeTab = getActiveTab();

    let targetData, currentPage;
    if (activeTab === 'pending') {
        targetData = pendingDocuments;
        currentPage = currentPendingPage;
    } else if (activeTab === 'unknown') {
        targetData = unknownPool;
        currentPage = currentUnknownPage;
    } else {
        targetData = processedDocuments.filter(doc => doc.categoryId === selectedCategoryId);
        currentPage = currentDocumentPage;
    }

    const finalData = targetData.filter(doc => doc.name.toLowerCase().includes(searchTerm));

    document.getElementById('docCount').textContent = processedDocuments.filter(d => d.categoryId === selectedCategoryId).length;
    document.getElementById('pendingCount').textContent = pendingDocuments.length;
    document.getElementById('unknownCount').textContent = unknownPool.length;

    const docsToRender = finalData.slice(0, currentPage * DOCS_PER_PAGE);
    const hasMore = finalData.length > docsToRender.length;

    const getDocCategoryName = (categoryId) => categories.find(c => c.id === categoryId)?.name || 'N/A';

    const renderDocItem = (doc) => {
        const docCategory = getDocCategoryName(doc.categoryId);
        let statusHtml, clickAction, actionButton = '';

        switch (doc.status) {
            case 'Processed':
                statusHtml = `<p class="text-sm text-gray-500 mt-1">Category: <span class="text-indigo-600 font-medium">${docCategory}</span></p>`;
                clickAction = `selectDocument('${doc.id}')`;
                break;
            case 'Pending':
            case 'Uploaded':
                statusHtml = `<p class="text-sm text-orange-500 flex items-center mt-1"><i data-lucide="loader" class="w-4 h-4 mr-1 animate-spin"></i> Ready to Process</p>`;
                clickAction = ``; // No main click action
                actionButton = `
                    <button onclick="processDocument(event, '${doc.id}')" class="text-green-500 hover:text-green-700 p-1" title="Process Document">
                        <i data-lucide="play-circle" class="w-5 h-5"></i>
                    </button>`;
                break;
            default: // Unknown
                statusHtml = `<p class="text-sm text-red-500 flex items-center mt-1"><i data-lucide="x-circle" class="w-4 h-4 mr-1"></i> Unknown: Review Needed</p>`;
                clickAction = ``; // Or some other action
                break;
        }

        return `
        <div class="p-3 bg-white rounded-xl border border-gray-200 hover:bg-gray-50 transition duration-150 group">
            <div ${clickAction ? `onclick="${clickAction}"` : ''} class="${clickAction ? 'cursor-pointer' : ''}">
                <p class="font-medium text-gray-800 truncate">${doc.name}</p>
                ${statusHtml}
            </div>
            <div class="flex justify-end mt-2 space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                ${actionButton}
                 <button onclick="archiveDocument(event, '${doc.id}')" class="text-red-500 hover:text-red-700 p-1" title="Archive Document">
                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                </button>
            </div>
        </div>`;
    };

    docListEl.innerHTML = activeTab === 'documents' ? docsToRender.map(renderDocItem).join('') : '';
    pendListEl.innerHTML = activeTab === 'pending' ? docsToRender.map(renderDocItem).join('') : '';
    unknownListEl.innerHTML = activeTab === 'unknown' ? docsToRender.map(renderDocItem).join('') : '';

    loadMoreBtn.classList.toggle('hidden', !hasMore);
    lucide.createIcons();
}

async function archiveDocument(event, docId) {
    event.stopPropagation(); 
    if (!confirm('Are you sure you want to archive this document?')) return;

    try {
        const updatedDoc = await api.delete(`/documents/${docId}`);
        const docIndex = documents.findIndex(d => d.id === docId);
        if (docIndex !== -1) {
            documents[docIndex] = updatedDoc;
        }
        updateDocumentPools();
        console.log(`Document ${updatedDoc.name} archived successfully.`);
    } catch (error) {
        console.error("Failed to archive document:", error);
    }
}


function renderKVTable() {
    const kvTableBody = document.getElementById('kvTableBody');
    if (!kvTableBody) return;

    kvTableBody.innerHTML = kvData.map((item, index) => `
        <tr id="kv-row-${index}">
            <td><input type="text" value="${item.key}" class="w-full p-1 border rounded text-sm bg-gray-50 kv-key" data-index="${index}"></td>
            <td><input type="text" value="${item.value}" class="w-full p-1 border rounded text-sm kv-value" data-index="${index}"></td>
            <td>
                <button onclick="deleteKVRow(${index})" class="text-red-500 hover:text-red-700 p-1">
                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                </button>
            </td>
        </tr>
    `).join('');
    lucide.createIcons();
}

function addKVRow() {
    kvData.push({ key: "New Key", value: "New Value" });
    renderKVTable();
}

function deleteKVRow(index) {
    kvData.splice(index, 1);
    renderKVTable();
}

async function saveKVData() {
    if (!currentDoc) return console.error("Document not ready.");

    const newKvData = Array.from(document.querySelectorAll('#kvTableBody tr')).map(row => ({
        key: row.querySelector('.kv-key').value.trim(),
        value: row.querySelector('.kv-value').value.trim(),
    })).filter(item => item.key);

    try {
        const updatedDoc = await api.post(`/documents/${currentDoc.id}/kv`, newKvData);
        const docIndex = documents.findIndex(d => d.id === currentDoc.id);
        if (docIndex !== -1) {
            documents[docIndex] = updatedDoc;
        }
        currentDoc = updatedDoc;
        kvData = updatedDoc.kv_data;
        renderKVTable();
        console.log(`KV data for ${currentDoc.name} saved successfully.`);
    } catch (error) {
        console.error("Failed to save KV data:", error);
    }
}

// --- View Switching ---
function updateMainViewInfo() {
    if (!currentDoc || currentDoc.status === 'Archived') {
        document.getElementById('currentDocName').textContent = 'No document selected';
        document.getElementById('currentDocCategory').textContent = '';
        kvData = [];
        renderKVTable();
        return;
    }
    const category = categories.find(c => c.id === currentDoc.categoryId);
    document.getElementById('currentDocName').textContent = currentDoc.name;
    document.getElementById('currentDocCategory').textContent = category ? category.name : 'Unknown';
    document.getElementById('chatModeStatus').textContent = `Current Document: ${currentDoc.name} (${category ? category.name : 'N/A'})`;

    kvData = currentDoc.kv_data || [];
    updateChatPrompt();
    renderKVTable();
}

function switchToView(viewId, docId = null) {
    document.querySelectorAll('#viewContainer > section').forEach(view => view.classList.add('hidden'));
    document.getElementById(viewId).classList.remove('hidden');

    if (docId) {
        currentDoc = documents.find(d => d.id === docId);
        if (viewId === 'viewA') updateMainViewInfo();
    } else if (viewId === 'viewC') {
        if (!currentDoc && processedDocuments.length > 0) currentDoc = processedDocuments[0];
        if (currentDoc) updateMainViewInfo();
    }

    if (window.innerWidth < 1024) document.getElementById('sidebar').classList.add('hidden');
}

function selectDocument(docId) {
    const doc = processedDocuments.find(d => d.id === docId);
    if (doc) {
        currentDoc = doc;
        switchToView('viewA', docId);
    }
}

function switchDocumentList(list) {
    const docTab = document.getElementById('tabDocuments');
    const pendTab = document.getElementById('tabPending');
    const unknownTab = document.getElementById('tabUnknown');

    docTab.classList.toggle('border-indigo-600', list === 'documents');
    docTab.classList.toggle('text-indigo-600', list === 'documents');
    pendTab.classList.toggle('border-indigo-600', list === 'pending');
    pendTab.classList.toggle('text-indigo-600', list === 'pending');
    unknownTab.classList.toggle('border-indigo-600', list === 'unknown');
    unknownTab.classList.toggle('text-indigo-600', list === 'unknown');

    document.getElementById('documentList').classList.toggle('hidden', list !== 'documents');
    document.getElementById('pendingList').classList.toggle('hidden', list !== 'pending');
    document.getElementById('unknownList').classList.toggle('hidden', list !== 'unknown');

    currentDocumentPage = 1;
    currentPendingPage = 1;
    currentUnknownPage = 1;
    renderDocumentLists();
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('hidden');
}

function toggleCategoryModal(show) {
    const modal = document.getElementById('categoryModal');
    modal.classList.toggle('hidden', !show);
    modal.classList.toggle('flex', show);
    if (show) renderExistingCategories();
}

function renderExistingCategories() {
    const container = document.getElementById('existingCategories');
    container.innerHTML = '<p class="text-sm text-gray-500 font-medium border-b pb-2">Existing Categories:</p>' +
        categories.map(cat => {
            const count = processedDocuments.filter(d => d.categoryId === cat.id).length;
            return `
                <div class="p-2 border rounded-lg bg-white text-sm">
                    <p class="font-medium text-gray-800">${cat.name} (${count} docs)</p>
                    <p class="text-xs text-gray-500 truncate">Training: ${cat.description || 'N/A'}</p>
                </div>
            `;
        }).join('');
}

async function addCategory() {
    const nameInput = document.getElementById('newCategoryName');
    const descInput = document.getElementById('newCategoryDescription');
    const name = nameInput.value.trim();
    const description = descInput.value.trim();

    if (!name || !description) return console.error("Name and description are required.");

    try {
        const newCategory = await api.post('/categories', { name, description });
        categories.push(newCategory);
        nameInput.value = '';
        descInput.value = '';
        updateDocumentPools();
        renderExistingCategories();
        console.log(`New Category Added: ${name}.`);
    } catch (error) {
        console.error("Failed to add category:", error);
    }
}

// --- Document Processing ---
async function processDocument(event, docId) {
    event.stopPropagation();
    showLoading(true);
    try {
        const updatedDoc = await api.post(`/documents/${docId}/process`);
        const docIndex = documents.findIndex(d => d.id === docId);
        if (docIndex !== -1) {
            documents[docIndex] = updatedDoc;
        }
        updateDocumentPools();
        console.log(`Document ${updatedDoc.name} processed successfully.`);
    } catch (error) {
        console.error("Failed to process document:", error);
    } finally {
        showLoading(false);
    }
}

async function handleFileUpload() {
    const fileInput = document.getElementById('documentUpload');
    if (fileInput.files.length === 0) return;

    if (!selectedCategoryId) {
        alert("Please select a category before uploading a document.");
        fileInput.value = ''; // Clear the file input
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('category', selectedCategoryId); // <-- FIX: Add category to the form data
    
    showLoading(true);
    try {
        const newDoc = await api.postFile('/uploads', formData); // <-- FIX: Handle single new doc
        documents.push(newDoc); // <-- FIX: Add to the existing array

        fileInput.value = ''; // Clear the file input
        updateDocumentPools();
        console.log(`Document '${newDoc.name}' uploaded successfully.`);
        // Switch to the pending tab to show the newly uploaded file
        switchDocumentList('pending');
    } catch (error) {
        console.error("File upload failed:", error);
        alert(`File upload failed. Please check the console for details.`);
    } finally {
        showLoading(false);
    }
}


// --- Chat Functions ---
async function sendGeneralChat() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text || !currentDoc) return;

    appendMessage('chatHistory', 'user', text);
    input.value = ''; // Clear input immediately

    try {
        const response = await api.post(`/chat/general`, { documentId: currentDoc.id, query: text });
        appendMessage('chatHistory', 'ai', response.answer);
    } catch (error) {
        console.error("Chat API error:", error);
        appendMessage('chatHistory', 'ai', "Sorry, I couldn't get a response.");
    }
}

async function sendKVChat() {
    const input = document.getElementById('kvChatInput');
    const text = input.value.trim();
    if (!text || !currentDoc) return;
    
    appendMessage('kvChatHistory', 'user', text);
    input.value = ''; // Clear input immediately

    try {
        const response = await api.post(`/chat/kv`, { documentId: currentDoc.id, query: text });
        appendMessage('kvChatHistory', 'ai', response.answer);
    } catch (error) {
        console.error("KV Chat API error:", error);
        appendMessage('kvChatHistory', 'ai', "Sorry, I couldn't get a response.");
    }
}

function appendMessage(historyId, sender, text) {
    const history = document.getElementById(historyId);
    const isUser = sender === 'user';
    history.innerHTML += `
        <div class="flex ${isUser ? 'justify-end' : 'justify-start'}">
            <div class="p-3 rounded-xl max-w-xs lg:max-w-md text-sm shadow ${isUser ? 'bg-indigo-500 text-white' : 'bg-gray-100 text-gray-800'}">
                ${text.replace(/\n/g, '<br>')}
            </div>
        </div>
    `;
    history.scrollTop = history.scrollHeight;
}

function updateChatPrompt() {
    const mode = document.getElementById('chatMode').value;
    const input = document.getElementById('chatInput');
    if (!currentDoc) return;
    const category = categories.find(c => c.id === currentDoc.categoryId)?.name || 'N/A';
    input.placeholder = mode === 'global'
        ? "Ask anything about the entire document..."
        : `Query relevant ${category} fields...`;
}

function toggleKVRefinementChat(show) {
    document.getElementById('kvRefinementChat').classList.toggle('translate-x-full', !show);
}

// --- Global Listeners ---
window.selectCategory = selectCategory;
window.switchToView = switchToView;
window.selectDocument = selectDocument;
window.switchDocumentList = switchDocumentList;
window.addKVRow = addKVRow;
window.deleteKVRow = deleteKVRow;
window.saveKVData = saveKVData;
window.toggleSidebar = toggleSidebar;
window.toggleCategoryModal = toggleCategoryModal;
window.addCategory = addCategory;
window.processDocument = processDocument;
window.sendGeneralChat = sendGeneralChat;
window.sendKVChat = sendKVChat;
window.updateChatPrompt = updateChatPrompt;
window.toggleKVRefinementChat = toggleKVRefinementChat;
window.handleFileUpload = handleFileUpload;
window.handleSearch = handleSearch;
window.loadMoreDocuments = loadMoreDocuments;
window.archiveDocument = archiveDocument;

// --- App Initialization ---
window.onload = initializeApp;
