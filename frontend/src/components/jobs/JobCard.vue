<script setup>
import { computed } from "vue";
import JobStatusBadge from "./JobStatusBadge.vue";

const props = defineProps({
  job: { type: Object, required: true },
});

const timeAgo = computed(() => {
  const diff = Date.now() - new Date(props.job.created_at);
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
});

const borderClass = computed(() => {
  if (props.job.priority === "emergency")
    return "border-red-500 dark:border-red-600";
  if (props.job.priority === "high")
    return "border-orange-400 dark:border-orange-500";
  return "border-gray-200 dark:border-gray-800";
});
</script>

<template>
  <RouterLink
    :to="`/jobs/${job.id}`"
    class="block bg-white dark:bg-gray-900 rounded-xl border shadow-sm hover:shadow-md transition p-5"
    :class="borderClass"
  >
    <!-- Top row: service type + time -->
    <div class="flex items-start justify-between gap-2 mb-2">
      <div class="flex items-center gap-1.5 min-w-0">
        <h3 class="font-semibold text-gray-900 dark:text-gray-100 text-sm leading-snug truncate">
          {{ job.service_type || "Service Request" }}
        </h3>
        <!-- AI-created badge -->
        <span
          v-if="job.call_sid"
          title="Created by AI voice assistant"
          class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-semibold
                 bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300 shrink-0"
        >
          <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13
                 a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0
                 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
          </svg>
          AI
        </span>
      </div>
      <span class="text-xs text-gray-400 dark:text-gray-500 shrink-0">{{ timeAgo }}</span>
    </div>

    <!-- Caller info -->
    <p class="text-xs text-gray-600 dark:text-gray-400 mb-1">
      {{ job.caller_name || "Unknown caller" }}
      &middot;
      {{ job.caller_phone }}
    </p>

    <!-- Address -->
    <a
      v-if="job.address"
      :href="`https://maps.google.com/maps?q=${encodeURIComponent(job.address + (job.city ? ', ' + job.city : ''))}`"
      target="_blank"
      rel="noopener"
      @click.stop
      class="block text-xs text-brand-600 dark:text-brand-400 hover:underline mb-3"
    >
      {{ job.address }}<span v-if="job.city">, {{ job.city }}</span>
    </a>

    <!-- Status + assigned tech -->
    <div class="flex items-center justify-between">
      <JobStatusBadge :status="job.status" :priority="job.priority" />
      <span
        v-if="job.assigned_tech_name"
        class="text-xs text-gray-500 dark:text-gray-400"
      >
        {{ job.assigned_tech_name }}
      </span>
      <span v-else class="text-xs text-gray-400 dark:text-gray-600"
        >Unassigned</span
      >
    </div>
  </RouterLink>
</template>
