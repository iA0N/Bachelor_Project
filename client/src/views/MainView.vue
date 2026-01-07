<script setup>
import Navbar from '../components/Navbar.vue'
import PDFViewer from '../components/PDFViewer.vue'
import FileUpload from '../components/FileUpload.vue'
import FooterBar from '../components/FooterBar.vue'
import { MainViewState } from '../js/MainViewState.ts'
import { ref, watch, useTemplateRef, nextTick } from 'vue';
import axios from 'axios'
import { marked } from 'marked';

let user_documents_search_term = ref("");
let current_document = ref(null);
let current_document_unaltered = ref(null);
let current_document_summary_sentences = ref(null);
let current_document_id = ref(null);
let current_document_file_name = null;
let current_document_num_pages = null;
let current_document_author = null;
let current_document_title = null;
let current_document_used_model = null;
let search_term = ref(""); // Updated through v model
let search_term_param = ref(""); // Only updated on search hit, passed down to child component
let username = "";
let csrf_token = '';
let user_docs = ref([]);
let filtered_user_docs = ref([]);
let selected_document_chat = ref([]);
let current_chat_message = ref("");
let chat_history = ref([]);
let message_loading = ref(false);
let selected_page = ref(1);
let user_models = ref([]);
let selected_summary_sentence_index = ref(null);
let selected_summary_sentence_candidate_index = ref(null);

let main_view_state = ref(MainViewState.WAITING_FOR_USER_DOCUMENT_SELECTION);

const chat_end = useTemplateRef('chat_end');
const top_of_page = useTemplateRef('top_of_page');


reset()

watch(current_document, (new_document) => {
    // yes, console.log() is a side effect
    //console.log(`new document is: ${new_document}`)
})

watch(user_documents_search_term, (current_user_documents_search_term) => {
    const user_documents_search_term_lower_case = current_user_documents_search_term.toLowerCase();
    filtered_user_docs.value = user_docs.value.filter(item => item.file_name.toLowerCase().includes(user_documents_search_term_lower_case));
})

async function check_login() {
    try {
        const res = await axios.get('http://localhost:8000/api/v1/login_status', {
            withCredentials: true,
            headers: {
                'Content-Type': 'application/json'
            },
        });
        let login_status = res.data['login_status'];
        console.log(login_status);
        if (login_status == false) {
            window.location.replace("http://localhost:8000");
        }
    } catch (error) {
        console.error('Error sending GET request:', error);
    }
}

check_login();

async function get_csrf_token() {
    try {
        const res = await axios.get('http://localhost:8000/api/v1/csrf', {
            withCredentials: true,
            headers: {
                'Content-Type': 'application/json'
            },
        });
        csrf_token = res.data['csrf_token'];
        console.log(csrf_token);
    } catch (error) {
        console.error('Error sending GET request:', error);
    }
}

get_csrf_token();

async function findInDocument(candidate) {
    await get_highlighted_pdf(candidate);
    search_term_param.value = candidate;
}

async function searchForSource(index) {
    selected_summary_sentence_index.value = index;
    let selected_sentence = current_document_summary_sentences.value[index];
    selected_sentence.candidates.sort((a, b) => b.confidence_score - a.confidence_score);
    selected_summary_sentence_candidate_index.value = 0;
    findInDocument(selected_sentence.candidates[0].candidate);
}

const fileUploadedEvent = async (file, dataUrl, model) => {
    storeDocumentAndSummarize(file.name, dataUrl, model)
};

const newModelEvent = async (repo_id, filename) => {
    createNewModel(repo_id, filename)
};

const removeModelEvent = async (model) => {
    removeModel(model)
};

async function clear_current_document_data() {
    current_document.value = null;
    current_document_id.value = null;
    current_document_summary_sentences.value = null;
    current_document_file_name = null;
    current_document_num_pages = null;
    current_document_author = null;
    current_document_used_model = null;
    current_document_title = null;
    current_document_unaltered.value = null;
    search_term.value = "";
    search_term_param.value = "";
    selected_summary_sentence_index.value = null;
    selected_summary_sentence_candidate_index.value = null;
    selected_document_chat.value = null;
    current_chat_message.value = "";
    chat_history.value = [];
    message_loading.value = false;
}

async function reset() {
    await clear_current_document_data();
    main_view_state.value = MainViewState.WAITING_FOR_USER_DOCUMENT_SELECTION;
    user_documents_search_term.value = "";
    user_docs.value = [];
    filtered_user_docs.value = [];
    await getUserDocuments();
    filtered_user_docs.value = user_docs.value;
    console.log("application ready");
}

async function get_highlighted_pdf(candidate) {
    const payload = {
        doc_id: current_document_id.value,
        search_term: candidate
    };

    try {
        const res = await axios.post('http://localhost:8000/api/v1/get_highlighted_pdf', payload, {
            withCredentials: true,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFTOKEN': csrf_token
            },
        });
        let returned_data_url = res.data['data_url'];
        selected_page.value = res.data['page_num_start'];
        current_document.value = returned_data_url;
    } catch (error) {
        console.error('Error sending POST request:', error);
    }
}

async function storeDocumentAndSummarize(file_name, document_data, model) {
    current_document_file_name = file_name;
    current_document.value = document_data;
    main_view_state.value = MainViewState.LOADING_DOCUMENT_AND_SUMMARY;

    const payload = {
        file_data: document_data,
        file_name: file_name,
        model: model
    };

    try {
        const res = await axios.post('http://localhost:8000/api/v1/store_and_summarize', payload, {
            withCredentials: true,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFTOKEN': csrf_token
            },
        });
        loadUserDocument(res.data['id']);
    } catch (error) {
        console.error('Error sending POST request:', error);
    }
}

async function createNewModel(repo_id, filename) {
    const payload = {
        repo_id: repo_id,
        filename: filename
    };

    try {
        const res = await axios.post('http://localhost:8000/api/v1/create_user_model', payload, {
            withCredentials: true,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFTOKEN': csrf_token
            },
        });
        console.log(res.data);
        getUserModels();
    } catch (error) {
        console.error('Error sending POST request:', error);
    }
}

async function removeModel(model) {
    const payload = {
        model: model,
    };

    try {
        const res = await axios.delete('http://localhost:8000/api/v1/remove_user_model/' + model, {
            withCredentials: true,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFTOKEN': csrf_token
            },
        });

        console.log(res.data);
        getUserModels();
    } catch (error) {
        console.error('Error sending POST request:', error);
    }
}

async function sendChat() {
    message_loading.value = true;
    chat_end.value.scrollIntoView({});
    top_of_page.value.scrollIntoView({});
    const payload = {
        doc_id: current_document_id.value,
        chat_msg: current_chat_message.value
    };

    current_chat_message.value = "";

    try {
        const res = await axios.post('http://localhost:8000/api/v1/send_chat', payload, {
            withCredentials: true,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFTOKEN': csrf_token
            },
        });
        message_loading.value = false;
        chat_history.value = res.data["chat_history"];
        await nextTick();
        chat_end.value.scrollIntoView({});
        top_of_page.value.scrollIntoView({});
    } catch (error) {
        console.error('Error sending POST request:', error);
    }
}

async function getUserDocuments() {
    try {
        const res = await axios.get('http://localhost:8000/api/v1/get_user_documents', {
            withCredentials: true,
            headers: {
                'Content-Type': 'application/json'
            },
        });
        // console.log(res.data['user_docs']);
        // let user_docs = res.data['user_docs'];
        // user_docs.forEach(doc => {
        //     let r = getUserDocument(doc['id']);
        //     console.log(r);
        // });
        user_docs.value = res.data['user_docs']
        console.log(user_docs.value)
    } catch (error) {
        console.error('Error sending GET request:', error);
    }
}

async function getUserDocument(doc_id) {

    try {
        const res = await axios.get('http://localhost:8000/api/v1/get_user_document/' + doc_id, {
            withCredentials: true,
            headers: {
                'Content-Type': 'application/json'
            },
        });
        console.log(res.data);
        return res.data
    } catch (error) {
        console.error('Error sending GET request:', error);
    }
}

async function setCurrentDocument(document_id, document_data, summary_sentences, document_file_name, document_title, document_author, document_num_pages, document_chat_history, document_used_model) {
    current_document_id.value = document_id;
    current_document_unaltered.value = document_data;
    current_document.value = document_data;
    current_document_summary_sentences.value = summary_sentences;
    current_document_file_name = document_file_name;
    current_document_author = document_author;
    current_document_used_model = document_used_model;
    current_document_title = document_title;
    current_document_num_pages = document_num_pages;
    chat_history.value = document_chat_history
    main_view_state.value = MainViewState.WAITING_FOR_USER_SENTENCE_SELECTION;
    chat_end.value.scrollIntoView({});
    top_of_page.value.scrollIntoView({});
}

async function loadUserDocument(doc_id) {
    let doc = await getUserDocument(doc_id);
    await setCurrentDocument(doc_id, doc.file_data, doc.summary, doc.file_name, doc.title, doc.author, doc.num_pages, doc.chat_history, doc.used_model);
}

async function deleteUserDocument(doc_id) {
    try {
        const res = await axios.delete('http://localhost:8000/api/v1/delete_user_document/' + doc_id, {
            withCredentials: true,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFTOKEN': csrf_token
            },
        });
        user_docs.value = user_docs.value.filter(item => item.id != doc_id);
        filtered_user_docs.value = filtered_user_docs.value.filter(item => item.id != doc_id);
    } catch (error) {
        console.error('Error sending DELETE request:', error);
    }
}

async function getUserModels() {

    try {
        const res = await axios.get('http://localhost:8000/api/v1/get_user_models', {
            withCredentials: true,
            headers: {
                'Content-Type': 'application/json'
            },
        });
        console.log(res.data);
        user_models.value = res.data['models']
    } catch (error) {
        console.error('Error sending GET request:', error);
    }
}

async function prev_candidate() {
    let selected_sentence = current_document_summary_sentences.value[selected_summary_sentence_index.value];
    let max_index = selected_sentence.candidates.length - 1
    if (selected_summary_sentence_candidate_index.value == 0) {
        selected_summary_sentence_candidate_index.value = max_index;
    }
    else {
        selected_summary_sentence_candidate_index.value -= 1;
    }
    findInDocument(selected_sentence.candidates[selected_summary_sentence_candidate_index.value].candidate);
}

async function next_candidate() {
    let selected_sentence = current_document_summary_sentences.value[selected_summary_sentence_index.value];
    let max_index = selected_sentence.candidates.length - 1
    if (selected_summary_sentence_candidate_index.value == max_index) {
        selected_summary_sentence_candidate_index.value = 0;
    }
    else {
        selected_summary_sentence_candidate_index.value += 1;
    }
    findInDocument(selected_sentence.candidates[selected_summary_sentence_candidate_index.value].candidate);
}

async function close_candidates() {
    selected_summary_sentence_index.value = null;
    selected_summary_sentence_candidate_index.value = null;
    current_document.value = current_document_unaltered.value;
}

getUserModels();

</script>

<template>
    <div class="overflow-hidden">
        <div ref="top_of_page"></div>
        <Navbar />

        <!-- SELECTION VIEW -->

        <!-- Mobile only -->
        <button data-drawer-target="mobile-sidebar" data-drawer-toggle="mobile-sidebar" aria-controls="mobile-sidebar"
            type="button"
            class="inline-flex items-center p-2 mt-2 ms-3 text-sm text-gray-500 rounded-lg sm:hidden hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-200 dark:text-gray-400 dark:hover:bg-gray-700 dark:focus:ring-gray-600">
            <span class="sr-only">Open sidebar</span>
            <svg class="w-6 h-6" aria-hidden="true" fill="currentColor" viewBox="0 0 20 20"
                xmlns="http://www.w3.org/2000/svg">
                <path clip-rule="evenodd" fill-rule="evenodd"
                    d="M2 4.75A.75.75 0 012.75 4h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 4.75zm0 10.5a.75.75 0 01.75-.75h7.5a.75.75 0 010 1.5h-7.5a.75.75 0 01-.75-.75zM2 10a.75.75 0 01.75-.75h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 10z">
                </path>
            </svg>
        </button>

        <!-- Previously uploaded document list -->
        <aside v-if="main_view_state === MainViewState.WAITING_FOR_USER_DOCUMENT_SELECTION" id="default-sidebar"
            class="fixed top-0 left-0 z-40 w-64 md:w-72 h-screen transition-transform -translate-x-full sm:translate-x-0"
            aria-label="Sidebar">
            <p></p>
            <div class="h-full px-3 pt-4 pb-24 overflow-y-auto bg-gray-50 dark:bg-gray-800 border mt-20">
                <p v-if="user_docs.length == 0" class="text-center text-gray-500 mt-14 text-md">
                    Your previously uploaded documents will appear here.
                </p>
                <div v-if="user_docs.length > 0">
                    <!--<p class="text-md font-normal text-gray-600 lg:text-lg dark:text-gray-400 text-start ps-1 mb-2">
                        Documents
                    </p>-->
                    <input type="search" v-model="user_documents_search_term"
                        class="block w-full p-2 ps-3 mb-2 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                        placeholder="Search your documents" />
                    <hr class="h-px my-2 bg-gray-400 border-0 dark:bg-gray-700">
                </div>
                <ul class="space-y-2 font-medium" v-if="user_docs != []">
                    <li v-for="doc in filtered_user_docs">
                        <div href="#" @click="loadUserDocument(doc.id)"
                            class="block max-w-sm p-2 bg-white border border-gray-400 rounded-lg shadow-sm hover:bg-gray-200 dark:bg-gray-800 dark:border-gray-700 dark:hover:bg-gray-700">
                            <a href="#"
                                class="flex items-center p-1 text-gray-900 transition duration-75 rounded-lg group">
                                <svg class="shrink-0 w-5 h-5 text-gray-500 transition duration-75 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-white"
                                    aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor"
                                    viewBox="0 0 16 20">
                                    <path
                                        d="M16 14V2a2 2 0 0 0-2-2H2a2 2 0 0 0-2 2v15a3 3 0 0 0 3 3h12a1 1 0 0 0 0-2h-1v-2a2 2 0 0 0 2-2ZM4 2h2v12H4V2Zm8 16H3a1 1 0 0 1 0-2h9v2Z" />
                                </svg>
                                <span class="ms-1 text-sm">{{ doc.file_name.substring(0, 20) }}</span>
                                <span class="text-end w-full" @click.stop="deleteUserDocument(doc.id)">ⓧ</span>
                            </a>
                            <span class="ms-0 text-xs">{{ doc.summary_teaser }}</span>
                            <br>
                            <span
                                class="bg-blue-100 text-blue-800 text-xs font-medium me-2 px-1.5 py-0.5 rounded-sm dark:bg-blue-900 dark:text-blue-300"
                                style="font-size: 10px;">{{ doc.used_model }}</span>
                        </div>
                    </li>
                </ul>
            </div>
        </aside>

        <div class="p-4 sm:ml-64">
            <div>
                <div v-if="main_view_state === MainViewState.WAITING_FOR_USER_DOCUMENT_SELECTION"
                    class="container mx-auto bg-gray">
                    <h1 class="mb-4 text-3xl font-extrabold text-gray-900 dark:text-white mt-5 text-center">
                        <span class="text-transparent bg-clip-text bg-gradient-to-r to-emerald-600 from-sky-400">
                            Find
                        </span>
                        the origin of
                        <span class="text-transparent bg-clip-text bg-gradient-to-r to-emerald-600 from-sky-400">
                            information
                        </span>
                        in your documents.
                    </h1>

                    <p class="text-lg font-normal text-gray-500 lg:text-xl dark:text-gray-400 text-center">
                        Upload a PDF to get results.
                    </p>
                    <p class="text-dm font-normal text-gray-500 lg:text-md dark:text-gray-400 text-center mt-3">
                        Generate summaries, find insights and retrieve probable information
                        sources within your documents.
                    </p>

                </div>

                <div v-if="main_view_state === MainViewState.WAITING_FOR_USER_DOCUMENT_SELECTION"
                    class="mt-20 md:w-1/2 mx-auto">
                    <FileUpload :user_models="user_models"
                        @uploaded="(file, dataUrl, model) => fileUploadedEvent(file, dataUrl, model)"
                        @new_model="(repo_id, filename) => newModelEvent(repo_id, filename)"
                        @remove_model="(model) => removeModelEvent(model)" />
                </div>
            </div>
        </div>


        <!-- DOCUMENT VIEW -->


        <div
            v-if="main_view_state === MainViewState.LOADING_DOCUMENT_AND_SUMMARY || main_view_state === MainViewState.WAITING_FOR_USER_SENTENCE_SELECTION">

            <div class="flex">
                <div class="w-1/2 text-center max-w-m p-12 pt-5">
                    <PDFViewer :file="current_document"
                    :search_term="search_term_param"
                    :current_document_num_pages="current_document_num_pages"
                    :selected_page="selected_page"
                    :current_document_summary_sentences="current_document_summary_sentences"
                    :selected_summary_sentence_index="selected_summary_sentence_index"
                    :selected_summary_sentence_candidate_index="selected_summary_sentence_candidate_index"
                    @prev_candidate="() => prev_candidate()"
                    @next_candidate="() => next_candidate()"
                    @close_candidates="() => close_candidates()"
                    />
                </div>

                <div class="py-4 pe-6 w-1/2">
                    <div class="mb-4">
                        <ul class="flex flex-wrap -mb-px text-sm font-medium text-center" id="default-tab"
                            data-tabs-toggle="#default-tab-content" role="tablist">
                            <li class="me-2" role="presentation">
                                <button class="inline-block p-4 border-b-2 rounded-t-lg" id="document-tab"
                                    data-tabs-target="#document" type="button" role="tab" aria-controls="document"
                                    aria-selected="false">Document</button>
                            </li>
                            <li class="me-2" role="presentation">
                                <button
                                    class="inline-block p-4 border-b-2 rounded-t-lg hover:text-gray-600 hover:border-gray-300 dark:hover:text-gray-300"
                                    id="chat-tab" data-tabs-target="#chat" type="button" role="tab" aria-controls="chat"
                                    aria-selected="false">Chat</button>
                            </li>
                        </ul>
                    </div>
                    <div id="default-tab-content">
                        <div class="hidden p-8 bg-white rounded-lg pb-6 dark:bg-gray-800" id="document" role="tabpanel"
                            aria-labelledby="document-tab">
                            <h2 class="mb-3 text-2xl font-extrabold tracking-tight text-gray-900 dark:text-white">
                                Document Information</h2>



                            <ul class="space-y-1 text-gray-800 list-disc list-inside dark:text-gray-400">
                                <li>
                                    Filename: <b>{{ current_document_file_name }}</b>
                                </li>
                                <li v-if="current_document_title">
                                    Title: <span class="text-sm"><b>{{ current_document_title }}</b></span>
                                </li>
                                <li v-if="current_document_author">
                                    Author: <b>{{ current_document_author }}</b>
                                </li>
                                <li v-if="current_document_num_pages">
                                    Number of pages: <b>{{ current_document_num_pages }}</b>
                                </li>
                            </ul>
                            <h2 class="mt-4 mb-3 text-2xl font-extrabold tracking-tight text-gray-900 dark:text-white">
                                Summary
                            </h2>

                            <div role="status" v-if="main_view_state === MainViewState.LOADING_DOCUMENT_AND_SUMMARY">
                                <svg aria-hidden="true"
                                    class="w-8 h-8 text-gray-200 animate-spin dark:text-gray-600 fill-blue-600"
                                    viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path
                                        d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
                                        fill="currentColor" />
                                    <path
                                        d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
                                        fill="currentFill" />
                                </svg>
                                <span class="sr-only">Loading...</span>
                            </div>

                            <div>
                                <p class="mb-3 text-gray-800 dark:text-gray-800"
                                    v-if="main_view_state === MainViewState.WAITING_FOR_USER_SENTENCE_SELECTION">
                                    <span v-for="(sentence, index) in current_document_summary_sentences"
                                        @click="searchForSource(index)">
                                        <span v-if="index == selected_summary_sentence_index" class="text-blue-600 cursor-pointer">
                                            {{ sentence.sentence }}&nbsp;
                                        </span>
                                        <span v-else class="hover:text-blue-600 cursor-pointer">
                                            {{ sentence.sentence }}&nbsp;
                                        </span>
                                    </span>
                                </p>
                            </div>

                            <div v-if="main_view_state === MainViewState.LOADING_DOCUMENT_AND_SUMMARY" class="mt-2">
                                <span class="text-gray-800">
                                    Please wait for the summary to finish and do not close the site.
                                </span>
                            </div>

                            <span class="text-sm" v-if="main_view_state === MainViewState.WAITING_FOR_USER_SENTENCE_SELECTION">Chat model:&nbsp;</span>
                            <span v-if="current_document_used_model"
                                class="bg-blue-100 text-blue-800 text-xs font-medium me-2 px-1.5 py-0.5 rounded-sm dark:bg-blue-900 dark:text-blue-300"
                                style="font-size: 12px;">{{ current_document_used_model }}
                            </span>

                            <br>
                            <a href="#" @click="reset"
                                v-if="main_view_state === MainViewState.WAITING_FOR_USER_SENTENCE_SELECTION"
                                class="inline-flex mt-4 items-center font-medium text-blue-600 hover:text-blue-800 dark:text-blue-500 dark:hover:text-blue-700">
                                Back to document selection
                                <svg class=" w-2.5 h-2.5 ms-2 rtl:rotate-180" aria-hidden="true"
                                    xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 6 10">
                                    <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                                        stroke-width="2" d="m1 9 4-4-4-4" />
                                </svg>
                            </a>
                        </div>

                        <div class="hidden p-2 bg-white rounded-lg" id="chat" role="tabpanel"
                            aria-labelledby="chat-tab">
                            <div
                                v-if="current_document_used_model != null && current_document_used_model != 'None'">
                                <div class="flex flex-col w-full overflow-hidden" style="height: 70vh;">
                                    <div class="flex-1 overflow-y-auto p-4 border space-y-2 bg-gray-200 rounded-xl"
                                        id="chat-window">

                                        <div v-for="chat_message in chat_history">
                                            <div v-if="chat_message.role === 'system'">
                                                <div class="flex items-start gap-2.5">
                                                    <div
                                                        class="flex flex-col w-full max-w-[320px] leading-1.5 p-4 border-gray-200 rounded-e-xl rounded-es-xl bg-gray-700">
                                                        <div class="flex items-center space-x-2 rtl:space-x-reverse">
                                                            <span class="text-sm font-semibold text-white">
                                                                The Sourcerer
                                                            </span>
                                                            <span class="text-sm font-normal text-gray-400"></span>
                                                        </div>
                                                        <div class="text-sm font-normal py-2.5 text-gray-900 text-white"
                                                            v-html="marked(chat_message.content)"></div>
                                                        <span v-if="current_document_used_model"
                                                            class="bg-blue-100 text-blue-800 text-xs font-medium me-2 px-1.5 py-0.5 rounded-sm dark:bg-blue-900 dark:text-blue-300"
                                                            style="font-size: 12px;">{{ current_document_used_model
                                                            }}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div v-if="chat_message.role === 'user'">
                                                <div class="flex items-start justify-end gap-2.5">
                                                    <div
                                                        class="flex flex-col w-full max-w-[320px] leading-1.5 p-4 border-blue-200 rounded-t-xl rounded-es-xl bg-blue-700">
                                                        <div class="flex items-center space-x-2 rtl:space-x-reverse">
                                                            <span class="text-sm font-semibold text-white">
                                                                You
                                                            </span>
                                                            <span class="text-sm font-normal text-gray-400"></span>
                                                        </div>
                                                        <div class="text-sm font-normal py-2.5 text-gray-900 text-white"
                                                            v-html="marked(chat_message.content)"></div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div role="status" class="flex justify-center m-4" v-if="message_loading">
                                            <svg aria-hidden="true"
                                                class="w-8 h-8 text-gray-200 animate-spin dark:text-gray-600 fill-blue-600"
                                                viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                <path
                                                    d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
                                                    fill="currentColor" />
                                                <path
                                                    d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
                                                    fill="currentFill" />
                                            </svg>
                                            <span class="sr-only">Loading...</span>
                                        </div>
                                        <div ref="chat_end">&nbsp;</div>
                                    </div>

                                    <div class="p-1">
                                        </input>
                                        <form class="mt-1 relative t-0" @submit.prevent="onSubmit">
                                            <label for="chat" class="sr-only">Your message</label>
                                            <div
                                                class="flex items-center px-3 py-2 rounded-lg bg-gray-200 dark:bg-gray-700">
                                                <textarea id="chat" rows="1" v-model="current_chat_message"
                                                    @keyup.enter="sendChat()"
                                                    class="block mx-4 p-2.5 w-full text-sm text-gray-900 bg-white rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                                                    placeholder="Your message..."></textarea>
                                                <button type="submit" @click.stop="sendChat()"
                                                    class="inline-flex justify-center p-2 text-blue-600 rounded-full cursor-pointer hover:bg-blue-100 dark:text-blue-500 dark:hover:bg-gray-600">
                                                    <svg class="w-5 h-5 rotate-90 rtl:-rotate-90" aria-hidden="true"
                                                        xmlns="http://www.w3.org/2000/svg" fill="currentColor"
                                                        viewBox="0 0 18 20">
                                                        <path
                                                            d="m17.914 18.594-8-18a1 1 0 0 0-1.828 0l-8 18a1 1 0 0 0 1.157 1.376L8 18.281V9a1 1 0 0 1 2 0v9.281l6.758 1.689a1 1 0 0 0 1.156-1.376Z" />
                                                    </svg>
                                                    <span class="sr-only">Send message</span>
                                                </button>
                                                <span class="sr-only">Send message</span>
                                            </div>
                                        </form>
                                    </div>
                                </div>
                            </div>
                            <div v-else class="p-6 bg-white rounded-lg pb-4 dark:bg-gray-800">
                                <p class="text-sm font-normal text-gray-800">
                                    This feature is only available if you select a model during document upload.
                                </p>
                                <a href="#" @click="reset"
                                    v-if="main_view_state === MainViewState.WAITING_FOR_USER_SENTENCE_SELECTION"
                                    class="inline-flex mt-4 items-center font-medium text-blue-600 hover:text-blue-800 dark:text-blue-500 dark:hover:text-blue-700">
                                    Back to document selection
                                    <svg class=" w-2.5 h-2.5 ms-2 rtl:rotate-180" aria-hidden="true"
                                        xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 6 10">
                                        <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                                            stroke-width="2" d="m1 9 4-4-4-4" />
                                    </svg>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <FooterBar />
    </div>
</template>
