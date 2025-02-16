<script setup>
import Navbar from '../components/Navbar.vue'
import PDFViewer from '../components/PDFViewer.vue'
import FileUpload from '../components/FileUpload.vue'
import FooterBar from '../components/FooterBar.vue'
import { ref, watch } from 'vue';
import axios from 'axios'

let uploaded_document = ref(null);
let uploaded_document_summary = ref(null);
let uploaded_document_summary_sentences = ref(null);
let uploaded_document_id = ref(null);
let file_name = "";
let search_term = ref(""); // Updated through v model
let search_term_param = ref(""); // Only updated on search hit, passed down to child component
let username = ""
let csrf_token = 'jj6dbsL01C1awa935a5qeX46hq1l0ndH'
let user_docs = ref(null)
reset()

watch(uploaded_document, (new_document) => {
    // yes, console.log() is a side effect
    //console.log(`new document is: ${new_document}`)
})

async function dosearch() {
    await get_highlighted_pdf();
    search_term_param.value = search_term.value;
}

const fileUploadedEvent = async (file, dataUrl, model) => {
    uploaded_document.value = dataUrl;
    file_name = file.name;
    storeDocumentAndQuerySummary(model)
    //console.log(file);
};

async function reset() {
    console.log("application ready");
    uploaded_document.value = null;
    uploaded_document_summary_sentences.value = null;
    uploaded_document_summary.value = null;
    file_name = "";
    search_term.value = null;
    search_term_param.value = null;
    await getUserDocuments()

}

async function get_highlighted_pdf() {
    const payload = {
        doc_id: uploaded_document_id.value,
        search_term: search_term.value
        // Add more key-value pairs as needed
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
        uploaded_document.value = returned_data_url;
    } catch (error) {
        console.error('Error sending POST request:', error);
    }
}

async function storeDocumentAndQuerySummary(model) {
    const payload = {
        file_data: uploaded_document.value,
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
        let summary = res.data['summary'];
        uploaded_document_summary_sentences.value = summary;
        uploaded_document_summary.value = summary.join(' ');
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
async function loadUserDocument(doc_id){
    let doc = await getUserDocument(doc_id);
    uploaded_document.value = doc.file_data;
    uploaded_document_summary_sentences = doc.summary;
    uploaded_document_summary.value = doc.summary.join(' ');
    uploaded_document_id.value = doc_id;
    file_name = doc.file_name;
    search_term.value = null;
    search_term_param.value = null;
}

</script>

<template>
    <div>
        <Navbar />
        <button data-drawer-target="default-sidebar" data-drawer-toggle="default-sidebar"
            aria-controls="default-sidebar" type="button"
            class="inline-flex items-center p-2 mt-2 ms-3 text-sm text-gray-500 rounded-lg sm:hidden hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-200 dark:text-gray-400 dark:hover:bg-gray-700 dark:focus:ring-gray-600">
            <span class="sr-only">Open sidebar</span>
            <svg class="w-6 h-6" aria-hidden="true" fill="currentColor" viewBox="0 0 20 20"
                xmlns="http://www.w3.org/2000/svg">
                <path clip-rule="evenodd" fill-rule="evenodd"
                    d="M2 4.75A.75.75 0 012.75 4h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 4.75zm0 10.5a.75.75 0 01.75-.75h7.5a.75.75 0 010 1.5h-7.5a.75.75 0 01-.75-.75zM2 10a.75.75 0 01.75-.75h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 10z">
                </path>
            </svg>
        </button>

        <aside v-if="uploaded_document == null" id="default-sidebar"
            class="fixed top-0 left-0 z-40 w-64 h-screen transition-transform -translate-x-full sm:translate-x-0"
            aria-label="Sidebar">
            <div class="h-full px-3 py-4 overflow-y-auto bg-gray-50 dark:bg-gray-800">
                <ul class="space-y-2 font-medium" v-if="user_docs != null">
                    <li>
                        <a href="#"
                            class="flex items-center p-2 text-gray-900 rounded-lg dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700 group">

                            <span
                                class="self-center text-2xl ms-4 font-semibold whitespace-nowrap dark:text-white">Source
                                Seeker</span>
                        </a>
                    </li>
                    <li v-for="doc in user_docs">

                        <a href="#" @click="loadUserDocument(doc.id)"
                            class="block max-w-sm p-2 bg-white border border-gray-400 rounded-lg shadow-sm hover:bg-gray-200 dark:bg-gray-800 dark:border-gray-700 dark:hover:bg-gray-700">
                            <a href="#"
                                class="flex items-center p-2 text-gray-900 transition duration-75 rounded-lg group">
                                <svg class="shrink-0 w-5 h-5 text-gray-500 transition duration-75 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-white"
                                    aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor"
                                    viewBox="0 0 16 20">
                                    <path
                                        d="M16 14V2a2 2 0 0 0-2-2H2a2 2 0 0 0-2 2v15a3 3 0 0 0 3 3h12a1 1 0 0 0 0-2h-1v-2a2 2 0 0 0 2-2ZM4 2h2v12H4V2Zm8 16H3a1 1 0 0 1 0-2h9v2Z" />
                                </svg>
                                <span class="ms-3 text-s">{{ doc.file_name }}</span>
                            </a>
                            <span class="ms-0 text-xs">{{ doc.summary_teaser }}</span>
                        </a>



                    </li>
                </ul>
            </div>
        </aside>

        <div class="p-4 sm:ml-64">
            <div>
                <div v-if="uploaded_document == null" class="container mx-auto bg-gray">
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

                <div v-if="uploaded_document == null" class="mt-20 lg:w-1/3 md:w-1/2 mx-auto">
                    <FileUpload @uploaded="(file, dataUrl, model) => fileUploadedEvent(file, dataUrl, model)" />
                </div>
            </div>
        </div>





        <div v-if="uploaded_document != null">

            <div class="columns-2">
                <div class="w-full text-center">
                    <PDFViewer :file="uploaded_document" :search_term="search_term_param" />
                </div>


                <div class="py-4 pe-6">
                    <div
                        class="w-full bg-white border border-gray-200 rounded-lg shadow dark:bg-gray-800 dark:border-gray-700">
                        <ul class="flex flex-wrap text-sm font-medium text-center text-gray-500 border-b border-gray-200 rounded-t-lg bg-gray-50 dark:border-gray-700 dark:text-gray-400 dark:bg-gray-800"
                            id="defaultTab" data-tabs-toggle="#defaultTabContent" role="tablist">
                            <li class="me-2">
                                <button id="document-tab" data-tabs-target="#document" type="button" role="tab"
                                    aria-controls="document" aria-selected="true"
                                    class="inline-block p-4 text-blue-600 rounded-ss-lg hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-blue-500">Document</button>
                            </li>
                            <li class="me-2">
                                <button id="search-tab" data-tabs-target="#search" type="button" role="tab"
                                    aria-controls="search" aria-selected="false"
                                    class="inline-block p-4 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-gray-300">Search</button>
                            </li>
                        </ul>
                        <div id="defaultTabContent">
                            <div class="hidden p-4 bg-white rounded-lg md:p-8 dark:bg-gray-800" id="document"
                                role="tabpanel" aria-labelledby="document-tab">
                                <h2 class="mb-3 text-2xl font-extrabold tracking-tight text-gray-900 dark:text-white">
                                    Document Information</h2>

                                <ul class="space-y-1 text-gray-800 list-disc list-inside dark:text-gray-400">
                                    <li>
                                        Filename: <b>{{ file_name }}</b>
                                    </li>
                                </ul>
                                <h2
                                    class="mt-4 mb-3 text-2xl font-extrabold tracking-tight text-gray-900 dark:text-white">
                                    Summary</h2>


                                <div role="status" v-if="uploaded_document_summary_sentences == null">
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


                                <p class="mb-3 text-gray-800 dark:text-gray-800"
                                    v-if="uploaded_document_summary_sentences != null">
                                    {{ uploaded_document_summary }}
                                </p>
                                
                                <p class="mb-3 text-gray-800 dark:text-gray-800"
                                    v-if="uploaded_document_summary_sentences != null">
                                    <span v-for="sentence in uploaded_document_summary_sentences" class="border border-gray-300 hover:bg-blue-300 cursor-pointer">{{ sentence }}</span>
                                </p>

                                <a href="#" @click="reset"
                                    class="inline-flex mt-2 items-center font-medium text-blue-600 hover:text-blue-800 dark:text-blue-500 dark:hover:text-blue-700">
                                    Upload another document
                                    <svg class=" w-2.5 h-2.5 ms-2 rtl:rotate-180" aria-hidden="true"
                                        xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 6 10">
                                        <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                                            stroke-width="2" d="m1 9 4-4-4-4" />
                                    </svg>
                                </a>
                            </div>
                            <div class="hidden p-4 bg-white rounded-lg md:p-8 dark:bg-gray-800" id="search"
                                role="tabpanel" aria-labelledby="search-tab">

                                <form class="mx-auto" @submit.prevent="onSubmit">
                                    <label for="defaultSearch"
                                        class="mb-2 text-sm font-medium text-gray-900 sr-only dark:text-white">Search</label>
                                    <div class="relative">
                                        <div
                                            class="absolute inset-y-0 start-0 flex items-center ps-3 pointer-events-none">
                                            <svg class="w-4 h-4 text-gray-500 dark:text-gray-400" aria-hidden="true"
                                                xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 20">
                                                <path stroke="currentColor" stroke-linecap="round"
                                                    stroke-linejoin="round" stroke-width="2"
                                                    d="m19 19-4-4m0-7A7 7 0 1 1 1 8a7 7 0 0 1 14 0Z" />
                                            </svg>
                                        </div>
                                        <input type="search" id="defaultSearch" v-model="search_term"
                                            class="block w-full p-4 ps-10 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                                            placeholder="Search in the uploaded document for information sources"
                                            required />
                                        <button type="submit" @click="dosearch"
                                            class="text-white absolute end-2.5 bottom-2.5 bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-4 py-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">Search</button>
                                    </div>
                                </form>

                                <hr class="mt-4">

                                <div v-if="search_term_param != ''">
                                    <h2 class="mb-2 mt-3 text-lg font-semibold text-gray-900 dark:text-white">Most
                                        probable
                                        information origins</h2>
                                    <ul class="space-y-1 mt-2 text-gray-500 list-inside dark:text-gray-400">
                                        <li class="flex items-center">
                                            <svg class="w-6 h-6 me-4 text-gray-800 dark:text-white" aria-hidden="true"
                                                xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none"
                                                viewBox="0 0 24 24">
                                                <path stroke="currentColor" stroke-linecap="round"
                                                    stroke-linejoin="round" stroke-width="2" d="m9 5 7 7-7 7" />
                                            </svg>

                                            <p>
                                                Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Phasellus
                                                facilisis odio
                                                sed mi. (98%)
                                                <button
                                                    class="inline-flex items-center ms-3 font-medium text-blue-600 hover:text-blue-800 dark:text-blue-500 dark:hover:text-blue-700">
                                                    View
                                                    <svg class=" w-2.5 h-2.5 ms-2 rtl:rotate-180" aria-hidden="true"
                                                        xmlns="http://www.w3.org/2000/svg" fill="none"
                                                        viewBox="0 0 6 10">
                                                        <path stroke="currentColor" stroke-linecap="round"
                                                            stroke-linejoin="round" stroke-width="2" d="m1 9 4-4-4-4" />
                                                    </svg>
                                                </button>
                                            </p>
                                        </li>
                                    </ul>
                                </div>

                            </div>
                        </div>
                    </div>
                </div>


            </div>


        </div>

        <FooterBar />
    </div>
</template>
