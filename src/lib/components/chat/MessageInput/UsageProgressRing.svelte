<script lang="ts">
    import { onMount, createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    export let limit = 0;
    export let used = 0;
    export let className = "size-5";
    
    // Dispatch a mount event when the component is mounted
    onMount(() => {
        dispatch('ringMount');
    });
    
    // Reactive declarations for calculations
    $: remaining = Math.max(0, limit - used);
    $: percentage = limit > 0 ? Math.max(0, Math.min(100, ((limit - used) / limit) * 100)) : 0;
    
    // Calculate the circle's properties
    $: radius = 8;
    $: circumference = 2 * Math.PI * radius;
    $: strokeDasharray = `${(percentage * circumference) / 100} ${circumference}`;
    
    // Calculate color based on remaining messages
    $: strokeColor = remaining >= limit * 0.5 ? 'rgb(34, 197, 94)' // green-500
        : remaining >= limit * 0.25 ? 'rgb(234, 179, 8)' // yellow-500
        : remaining >= 10 ? 'rgb(249, 115, 22)' // orange-500
        : 'rgb(239, 68, 68)'; // red-500
</script>

<svg class="{className} -rotate-90" viewBox="0 0 20 20">
    <!-- Background circle -->
    <circle
        cx="10"
        cy="10"
        r={radius}
        class="fill-none stroke-gray-200 dark:stroke-gray-700"
        stroke-width="2"
    />
    <!-- Progress circle -->
    <circle
        cx="10"
        cy="10"
        r={radius}
        class="fill-none transition-all duration-300"
        stroke-width="2"
        stroke-linecap="round"
        style="stroke: {strokeColor}; stroke-dasharray: {strokeDasharray};"
    />
</svg>