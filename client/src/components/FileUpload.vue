<script setup>
import { onMounted, ref } from 'vue'
import { initFlowbite } from 'flowbite'
import { list } from 'postcss';

let pdf_upload = null;
let show_delete_button = ref(false)

const emit = defineEmits(['uploaded', 'new_model', 'remove_model'])
const default_models = ["None"]

onMounted(() => {
    initFlowbite();
})

const props = defineProps({
    user_models: Array
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

function handleNewModel() {
    const $repo_id = document.querySelector('#repo_id');
    const $filename = document.querySelector('#filename');
    const $close_modal = document.querySelector('#close_modal');
    // console.log("New MODEL " + $repo_id.value + " " + $filename.value);
    emit('new_model', $repo_id.value, $filename.value);
    $repo_id.value = "";
    $filename.value = "";
    $close_modal.click()
}

function handleRemoveModel() {
    const $model = document.querySelector('#models');
    console.log("handle remove model");
    emit('remove_model', $model.value);
    show_delete_button.value = false;
}

function getFileData() {
    const $input = document.querySelector('#dropzone-file');
    let file = $input.files[0];
    if (file) {
        console.log(file);
    }
}

function checkDeletability() {
    const $model = document.querySelector('#models');
    console.log("checking")
    console.log($model.value)
    console.log(default_models)
    
    if (default_models.includes($model.value)) {
        show_delete_button.value = false;
    } else {
        show_delete_button.value = true;
    }
}

</script>

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
        <label for="models" class="block mt-5 mb-2 text-sm font-medium text-gray-900 dark:text-white">
            Select chat model
        </label>
        <div class="flex items-center space-x-2">
            <select id="models" @change="checkDeletability()"
                class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500">
                <option v-for="model in default_models">{{ model }}</option>
                <option v-for="model in props.user_models">{{ model }}</option>
            </select>

            <button type="button" data-modal-target="crud-modal" data-modal-toggle="crud-modal"
                class="text-white bg-blue-600 hover:bg-blue-700 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-full text-sm p-1.5 text-center inline-flex items-center me-2">
                <svg class="w-6 h-6 text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="12"
                    height="12" fill="none" viewBox="0 0 24 24">
                    <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M5 12h14m-7 7V5" />
                </svg>
                <span class="sr-only">Add model</span>
            </button>
            <button type="button" @click="handleRemoveModel()" v-if="show_delete_button"
                class="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-full text-sm p-1.5 text-center inline-flex items-center me-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">
                <svg class="w-[24px] h-[24px] text-white" aria-hidden="true"
                    xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
                    <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M5 7h14m-9 3v8m4-8v8M10 3h4a1 1 0 0 1 1 1v3H9V4a1 1 0 0 1 1-1ZM6 7h12v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V7Z" />
                </svg>
                <span class="sr-only">Remove model</span>
            </button>
        </div>
    </div>

    <!-- Main modal -->
    <div id="crud-modal" tabindex="-1" aria-hidden="true"
        class="hidden overflow-y-auto overflow-x-hidden fixed top-0 right-0 left-0 z-50 justify-center items-center w-full md:inset-0 h-[calc(100%-1rem)] max-h-full">
        <div class="relative p-4 w-full max-w-md max-h-full">
            <!-- Modal content -->
            <div class="relative bg-white rounded-lg shadow-sm dark:bg-gray-700">
                <!-- Modal header -->
                <div
                    class="flex items-center justify-between p-4 md:p-5 border-b rounded-t dark:border-gray-600 border-gray-200">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                        Add model
                    </h3>
                    <button type="button" id="close_modal"
                        class="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm w-8 h-8 ms-auto inline-flex justify-center items-center dark:hover:bg-gray-600 dark:hover:text-white"
                        data-modal-toggle="crud-modal">
                        <svg class="w-3 h-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none"
                            viewBox="0 0 14 14">
                            <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6" />
                        </svg>
                        <span class="sr-only">Close modal</span>
                    </button>
                </div>
                <!-- Modal body -->
                <form class="p-4 md:p-5">
                    <p class="text-xs text-gray-900 dark:text-white">
                        <b>Sourcerer</b> supports adding new models from huggingface.
                    </p>
                    <br>
                    <div class="grid gap-4 mb-4 grid-cols-2">
                        <div class="col-span-2">
                            <label for="repo_id"
                                class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Repository</label>
                            <input type="text" name="repo_id" id="repo_id"
                                class="bg-gray-50 border border-gray-300 text-gray-900 mb-2 text-sm rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:bg-gray-600 dark:border-gray-500 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500"
                                placeholder="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF" required="">

                            <label for="filename"
                                class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Filename</label>
                            <input type="text" name="filename" id="filename"
                                class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:bg-gray-600 dark:border-gray-500 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500"
                                placeholder="Meta-Llama-3.1-8B-Instruct-Q6_K.gguf" required="">
                        </div>
                    </div>
                    <button type="button" @click="handleNewModel()"
                        class="text-white inline-flex items-center bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">
                        <svg class="me-1 -ms-1 w-5 h-5" fill="currentColor" viewBox="0 0 20 20"
                            xmlns="http://www.w3.org/2000/svg">
                            <path fill-rule="evenodd"
                                d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z"
                                clip-rule="evenodd"></path>
                        </svg>
                        Add new model
                    </button>
                </form>
            </div>
        </div>
    </div>
</template>