<template>
    <div>
        <div class="flex items-center justify-center w-full mt-4">
            <label for="dropzone-file"
                class="flex flex-col items-center justify-center w-full h-64 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 dark:hover:bg-gray-800 dark:bg-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:hover:border-gray-500 dark:hover:bg-gray-600">
                <div class="flex flex-col items-center justify-center pt-5 pb-6">
                    <svg class="w-8 h-8 mb-4 text-gray-500 dark:text-gray-400" aria-hidden="true"
                        xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16">
                        <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2" />
                    </svg>
                    <p class="mb-2 text-sm text-gray-500 dark:text-gray-400"><span class="font-semibold">Click to
                            upload</span> or drag and drop</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">PDF</p>
                </div>
                <input id="dropzone-file" type="file" class="hidden" @change="handleFileUpload" />
            </label>
        </div>
        <label for="models" class="block mt-5 mb-2 text-sm font-medium text-gray-900 dark:text-white">Select model to generate summary</label>
        <select id="models"
            class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500">
            <option value="facebook/bart-large-cnn" selected>Bart Large CNN (Fast)</option>
            <option value="Meta-Llama-3.1-8B-Instruct-Q8_0.gguf">Meta Llama 3.1 8B (Slower)</option>
            <option value="llama-bart-combined">Combined pipeline (Slow)</option>
            <option value="demo">Demo</option>
            
        </select>
    </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { initFlowbite } from 'flowbite'

let pdf_upload = null;

const emit = defineEmits(['uploaded'])



onMounted(() => {
    initFlowbite();
})

function handleFileUpload(event) {
    const $input = document.querySelector('#dropzone-file');
    const $model = document.querySelector('#models');
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            pdf_upload = e.target.result;
            emit('uploaded', $input.files[0], pdf_upload, $model.value)
            console.log(e.target.result);
        };
        reader.readAsDataURL(file);
        // console.log(file);
    }
}

function getFileData() {
    const $input = document.querySelector('#dropzone-file');
    let file = $input.files[0];
    if (file) {
        console.log(file);
    }
}
</script>