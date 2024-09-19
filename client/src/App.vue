<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { onMounted } from 'vue'
import { initFlowbite } from 'flowbite'

import Navbar from './components/Navbar.vue'

// initialize components based on data attribute selectors
onMounted(() => {
    initFlowbite();

    let dark = false

    // On page load or when changing themes, best to add inline in `head` to avoid FOUC
    if (dark) {
        if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark')
        }
    }
})

</script>

<template>
    <Navbar />
    <RouterView />
</template>
