<script setup>
import PDFViewer from '../components/PDFViewer.vue'
import FileUpload from '../components/FileUpload.vue'
import FooterBar from '../components/FooterBar.vue'
import { ref, watch } from 'vue';
import axios from 'axios'

let uploaded_document = ref(null);
let file_name = "";
let search_term = ref(""); // Updated through v model
let search_term_param = ref(""); // Only updated on search hit, passed down to child component

watch(uploaded_document, (new_document) => {
    // yes, console.log() is a side effect
    //console.log(`new document is: ${new_document}`)
})

async function dosearch() {
    await queryAPI();
    search_term_param.value = search_term.value;
}

const fileUploadedEvent = async (file, dataUrl) => {
    uploaded_document.value = dataUrl;
    file_name = file.name;
    //console.log(file);
};

async function queryAPI() {
    const payload = {
        pdf_data: uploaded_document.value,
        // Add more key-value pairs as needed
    };

    try {
        const res = await axios.post('http://localhost:8000/api/v1/highlight_pdf', payload, {
            headers: {
                'Content-Type': 'application/json',
            },
        });
        let returned_data_url = res.data['data_url'];
        uploaded_document.value = returned_data_url;
    } catch (error) {
        console.error('Error sending POST request:', error);
    }
}

</script>

<template>
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
            <FileUpload @uploaded="(file, dataUrl) => fileUploadedEvent(file, dataUrl)" />
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
                                <button id="about-tab" data-tabs-target="#about" type="button" role="tab"
                                    aria-controls="about" aria-selected="true"
                                    class="inline-block p-4 text-blue-600 rounded-ss-lg hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-blue-500">About</button>
                            </li>
                            <li class="me-2">
                                <button id="search-tab" data-tabs-target="#search" type="button" role="tab"
                                    aria-controls="search" aria-selected="false"
                                    class="inline-block p-4 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-gray-300">Search</button>
                            </li>
                        </ul>
                        <div id="defaultTabContent">
                            <div class="hidden p-4 bg-white rounded-lg md:p-8 dark:bg-gray-800" id="about"
                                role="tabpanel" aria-labelledby="about-tab">
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
                                <p class="mb-3 text-gray-800 dark:text-gray-800">
                                    Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Phasellus facilisis odio
                                    sed mi.
                                    Curabitur suscipit. Nullam vel nisi. Etiam semper ipsum ut lectus. Proin aliquam,
                                    erat eget
                                    pharetra commodo, eros mi condimentum quam, sed commodo justo quam ut velit.
                                </p>
                                <a href="#"
                                    class="inline-flex items-center font-medium text-blue-600 hover:text-blue-800 dark:text-blue-500 dark:hover:text-blue-700">
                                    Learn more
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
