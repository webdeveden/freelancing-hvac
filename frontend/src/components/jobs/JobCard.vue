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
      <h3
        class="font-semibold text-gray-900 dark:text-gray-100 text-sm leading-snug"
      >
        {{ job.service_type || "Service Request" }}
      </h3>
      <span class="text-xs text-gray-400 dark:text-gray-500 shrink-0">{{
        timeAgo
      }}</span>
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
