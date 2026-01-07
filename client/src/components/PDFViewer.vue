<template>
    <div class="flex items-center justify-between bg-gray-200 border-b-2 border-blue-500 p-2 shadow rounded-t-md max-w-102">
        <div class="flex items-center space-x-2">
            <button class="px-3 py-1 bg-white border rounded hover:bg-gray-200" id="prevPage" @click="prevPage()">
                ← Prev
            </button>
            <span id="pageInfo" class="text-sm min-w-24">Page {{ current_page }} of {{ current_document_num_pages }}
            </span>
            <button class="px-3 py-1 bg-white border rounded hover:bg-gray-200" id="nextPage" @click="nextPage()">
                Next →
            </button>
        </div>

        <div class="flex items-center space-x-2">
            <button class="px-3 py-1 bg-white border rounded hover:bg-gray-200" id="zoomOut" @click="zoomOut()">
                ➖
            </button>
            <span id="zoomLevel" class="text-sm">{{ total_scale.toFixed(2) }}</span>
            <button class="px-3 py-1 bg-white border rounded hover:bg-gray-200" id="zoomIn" @click="zoomIn()">
                ➕
            </button>
        </div>
    </div>
    <div class="flex justify-end" v-if="selected_summary_sentence_index != null">
        <div class="mt-2 bg-gray-200 max-w-74 border rounded">
            <div class="p-2">
                <span class="text-sm me-8">
                    Candidate: {{ selected_summary_sentence_candidate_index + 1 }} / {{ current_document_summary_sentences[selected_summary_sentence_index].candidates.length }} 
                </span>
                <button class="ml-2 px-3 me-1 bg-white border rounded hover:bg-gray-200" id="searchPrev" @click="emit('prev_candidate')">
                    ◀
                </button>
                <button class="px-3 bg-white border rounded hover:bg-gray-200" id="searchNext" @click="emit('next_candidate')">
                    ▶
                </button>
                <button class="ml-2 ms-4 text-gray-500 hover:text-gray-800" id="closeSearch" @click="emit('close_candidates')">
                    ✕
                </button>
                <br>
                <span class="text-sm">
                    Confidence score: {{ current_document_summary_sentences[selected_summary_sentence_index].candidates[selected_summary_sentence_candidate_index].confidence_score }}
                </span>
            </div>
        </div>
    </div>
    <div>
        <CandidateSelector />
    </div>

    <div class="container">
        <div id="pdf-container">
            <canvas id="the-canvas" class="mx-auto"></canvas>
            <canvas id="highlight-canvas"></canvas>
        </div>
    </div>
</template>

<script setup>

import CandidateSelector from '@/components/CandidateSelector.vue'
import { onMounted, onUpdated, ref, watch } from 'vue'
import { initFlowbite } from 'flowbite'
import * as pdfjsLib from "pdfjs-dist/build/pdf";
import pdfWorker from "pdfjs-dist/build/pdf.worker?url";

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

const props = defineProps({
    file: String,
    search_term: String,
    selected_page: Number,
    current_document_num_pages: Number,
    current_document_summary_sentences: Object,
    selected_summary_sentence_index: Number,
    selected_summary_sentence_candidate_index: Number,
})

const emit = defineEmits(['prev_candidate', 'next_candidate'])

let pdf = null;
let current_page = ref(1);

let canvas = ref(null);
let context = null;
let highlightCanvas = ref(null);
let highlightContext = null;

let dyn_scale = ref(0.1);
let zoom = 0;
let total_scale = ref(0.1);

function updateTotalScale() {
    total_scale.value = dyn_scale.value + zoom;
}

function updateDynScale() {
    dyn_scale.value = window.innerWidth / 4000;
}

const updateScale = () => {
    if (pdf != null) {
        updateDynScale();
        updateTotalScale();
        if (current_page.value != null) {
            renderPage(current_page.value);
        }
    }
};

onMounted(() => {
    updateScale(); // Set initial scale
    window.addEventListener("resize", updateScale);

    initFlowbite();

    canvas.value = document.getElementById('the-canvas');
    context = canvas.value.getContext('2d');

    highlightCanvas.value = document.getElementById('highlight-canvas');
    highlightContext = highlightCanvas.value.getContext('2d');

    loadDocument();
    updateDynScale();
    updateTotalScale();
    console.log("Chat divisor:");
    console.log(window.devicePixelRatio);
    console.log(window.innerWidth);
});

watch(() => props.file, async () => {
    if (props.file) {
        await loadDocument();
    }
});

// watch(() => props.search_term, async () => {
//     if (props.search_term) {
//         await loadDocument();
//     }
// });

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

function zoomIn() {
    zoom += 0.1;
    updateTotalScale();
    renderPage(current_page.value);
}

function zoomOut() {
    zoom -= 0.1;
    updateTotalScale();
    renderPage(current_page.value);
}

async function loadDocument() {
    pdfjsLib.getDocument(props.file).promise.then(async function (loaded_document) {
        pdf = loaded_document;

        if (props.search_term != "") {
            current_page.value = props.selected_page
            //let page_number = await getFirstOccurrence()
            // if (page_number != -1) {
            //    current_page.value = page_number;
            // }
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
        const viewport = page.getViewport({ scale: 2 });
        canvas.value.height = viewport.height;
        canvas.value.width = viewport.width;
        highlightCanvas.value.height = viewport.height;
        highlightCanvas.value.width = viewport.width;

        canvas.value.style.width = viewport.width * total_scale.value + 'px';

        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };

        page.render(renderContext);
    });
}


function renderTextLayer(page, viewport) {
    page.getTextContent().then(function (textContent) {
        highlightContext.clearRect(0, 0, highlightCanvas.value.width, highlightCanvas.value.height);
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