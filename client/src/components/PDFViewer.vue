<template>
    <button type="button" @click="prevPage()"
        class="text-white bg-blue-700 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 font-medium rounded-full text-sm px-3 py-2 text-center me-2 mb-1 mt-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">
        < </button>
            <button type="button"
                class="text-gray-900 bg-white border border-gray-300 focus:outline-none hover:bg-gray-100 focus:ring-4 focus:ring-gray-100 font-medium rounded-full text-sm px-5 py-2.5 me-2 mb-2 dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:border-gray-600 dark:focus:ring-gray-700">
                {{ current_page }}
            </button>
            <button type="button" @click="nextPage()"
                class="text-white bg-blue-700 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 font-medium rounded-full text-sm px-3 py-2 text-center me-2 mb-1 mt-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">
                >
            </button>
            <div class="container">
                <div id="pdf-container" v-if="true">
                    <canvas id="the-canvas" class="mx-auto"></canvas>
                    <canvas id="highlight-canvas"></canvas>
                </div>
            </div>
</template>

<script setup>
import { onMounted, onUpdated, ref, watch } from 'vue'
import * as pdfjsLib from '/js/pdf.mjs?url'; // Import PDF.js library
import { initFlowbite } from 'flowbite'

const props = defineProps({
    file: String,
    search_term: String
})

let pdf = null;
let current_page = ref(1);

let canvas = null;
let context = null;
let highlightCanvas = null;
let highlightContext = null;

pdfjsLib.GlobalWorkerOptions.workerSrc = 'js/pdf.worker.mjs';

onMounted(() => {
    initFlowbite();

    canvas = document.getElementById('the-canvas');
    context = canvas.getContext('2d');

    highlightCanvas = document.getElementById('highlight-canvas');
    highlightContext = highlightCanvas.getContext('2d');

    loadDocument();
})

onUpdated(() => {
    if (props.search_term != "") {
        loadDocument();
    }
})

function prevPage() {
    if (current_page.value > 1) {
        current_page.value--;
    } else {
        current_page.value = pdf.numPages;
    }
    renderPage(current_page.value);
}

function nextPage() {
    if (pdf.numPages > current_page.value) {
        current_page.value++;
    } else {
        current_page.value = 1;
    }
    renderPage(current_page.value);
}

async function loadDocument() {
    pdfjsLib.getDocument(props.file).promise.then(async function (loaded_document) {
        pdf = loaded_document;

        if (props.search_term != "") {
            let page_number = await getFirstOccurrence()
            if (page_number != -1) {
                current_page.value = page_number;
            }
        }

        renderPage(current_page.value);
    });
}

async function getFirstOccurrence() {
    for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        const strings = textContent.items.map(item => item.str);
        const text = strings.join(' ');

        if (text.includes(props.search_term)) {
            let page_number = i;
            return page_number;
        }
    }
    return -1;
}


function renderPage(pageNumber) {
    pdf.getPage(pageNumber).then(function (page) {
        const viewport = page.getViewport({ scale: 1 });
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        highlightCanvas.height = viewport.height;
        highlightCanvas.width = viewport.width;

        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };

        page.render(renderContext).promise.then(function () {
            //renderTextLayer(page, viewport);
        });
    });
}


function renderTextLayer(page, viewport) {
    page.getTextContent().then(function (textContent) {
        highlightContext.clearRect(0, 0, highlightCanvas.width, highlightCanvas.height);
        textContent.items.forEach(item => {
            const transform = pdfjsLib.Util.transform(viewport.transform, item.transform);
            console.log(transform);
            const x = transform[4];
            const y = transform[5];
            //const fontHeight = transform[5] - transform[3];
            //const width = item.width * viewport.scale;
            //const height = fontHeight;

            if (item.str.includes(props.search_term)) {
                highlightContext.fillStyle = 'yellow';
                highlightContext.fillRect(x, y - 20, 800, 40);
            }
        });
    });
}

</script>

<style>
#pdf-container {
    position: relative;
    margin-top: 10px;
    margin-left: 10px;
}

#the-canvas {
    border: 1px solid black;
}

#highlight-canvas {
    position: absolute;
    top: 0;
    left: 0;
    pointer-events: none;
}
</style>