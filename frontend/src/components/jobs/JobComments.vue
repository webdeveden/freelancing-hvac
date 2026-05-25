<script setup>
/**
 * JobComments.vue — Markdown comment box for a job
 *
 * Write tab: raw markdown textarea
 * Preview tab: rendered HTML via marked.js
 * Comment list: all existing comments, reverse-chronological, with delete control
 */
import { ref, onMounted, computed } from 'vue'
import { marked }           from 'marked'
import { useAuthStore }     from '../../stores/auth.store.js'
import jobsService          from '../../services/jobs.service.js'

const props = defineProps({
  jobId: { type: Number, required: true },
})
const emit = defineEmits(['comment-added', 'comment-deleted'])

const auth     = useAuthStore()
const comments = ref([])
const draft    = ref('')
const tab      = ref('write')   // 'write' | 'preview'
const posting  = ref(false)

const previewHtml = computed(() => marked.parse(draft.value || '*Nothing to preview yet*'))

onMounted(fetchComments)

async function fetchComments() {
  const data  = await jobsService.getComments(props.jobId)
  comments.value = data.comments
}

async function submitComment() {
  if (!draft.value.trim()) return
  posting.value = true
  try {
    const data = await jobsService.addComment(props.jobId, draft.value)
    comments.value.push(data.comment)
    draft.value = ''
    tab.value   = 'write'
    emit('comment-added', data.comment)
  } finally {
    posting.value = false
  }
}

async function deleteComment(commentId) {
  await jobsService.deleteComment(props.jobId, commentId)
  comments.value = comments.value.filter(c => c.id !== commentId)
  emit('comment-deleted', commentId)
}

function canDelete(comment) {
  return auth.isAdmin || comment.author_id === auth.user?.id
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}
</script>

<template>
  <div class="mt-8">
    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 uppercase tracking-wide">
      Comments
    </h3>

    <!-- Comment editor -->
    <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden mb-6">
      <!-- Tabs -->
      <div class="flex border-b border-gray-200 dark:border-gray-800">
        <button
          @click="tab = 'write'"
          class="px-4 py-2 text-sm font-medium transition"
          :class="tab === 'write'
            ? 'text-brand-600 border-b-2 border-brand-600 bg-brand-50 dark:bg-brand-950/30'
            : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'"
        >
          Write
        </button>
        <button
          @click="tab = 'preview'"
          class="px-4 py-2 text-sm font-medium transition"
          :class="tab === 'preview'
            ? 'text-brand-600 border-b-2 border-brand-600 bg-brand-50 dark:bg-brand-950/30'
            : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'"
        >
          Preview
        </button>
        <div class="flex-1 flex items-center justify-end px-3">
          <span class="text-xs text-gray-400 dark:text-gray-500">Markdown supported</span>
        </div>
      </div>

      <!-- Write tab -->
      <div v-show="tab === 'write'" class="p-3">
        <textarea
          v-model="draft"
          placeholder="Leave a note... Markdown is supported.&#10;&#10;**Bold**, _italic_, `code`, - list items"
          rows="4"
          class="w-full text-sm bg-transparent text-gray-900 dark:text-gray-100
                 placeholder-gray-400 dark:placeholder-gray-600
                 focus:outline-none resize-none"
        />
      </div>

      <!-- Preview tab -->
      <div
        v-show="tab === 'preview'"
        class="p-4 min-h-24 prose prose-sm max-w-none dark:prose-invert markdown-body text-sm
               text-gray-800 dark:text-gray-200"
        v-html="previewHtml"
      />

      <!-- Footer -->
      <div class="flex justify-end px-3 py-2 border-t border-gray-200 dark:border-gray-800">
        <button
          @click="submitComment"
          :disabled="!draft.trim() || posting"
          class="px-4 py-1.5 text-sm font-medium bg-brand-600 hover:bg-brand-700
                 text-white rounded-lg disabled:opacity-50 transition"
        >
          {{ posting ? 'Posting...' : 'Post Comment' }}
        </button>
      </div>
    </div>

    <!-- Comment list -->
    <div v-if="comments.length" class="space-y-4">
      <div
        v-for="comment in comments"
        :key="comment.id"
        class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4"
      >
        <!-- Header -->
        <div class="flex items-start justify-between mb-2">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded-full bg-brand-100 dark:bg-brand-900 flex items-center justify-center">
              <span class="text-xs font-bold text-brand-700 dark:text-brand-300">
                {{ (comment.author_name || 'U').charAt(0).toUpperCase() }}
              </span>
            </div>
            <div>
              <span class="text-sm font-medium text-gray-900 dark:text-gray-100">
                {{ comment.author_name || 'Unknown' }}
              </span>
              <span class="ml-1.5 text-xs text-gray-400 dark:text-gray-500 capitalize">
                {{ comment.author_role }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs text-gray-400 dark:text-gray-500">{{ formatDate(comment.created_at) }}</span>
            <button
              v-if="canDelete(comment)"
              @click="deleteComment(comment.id)"
              class="p-1 rounded hover:bg-red-50 dark:hover:bg-red-950 text-gray-400 hover:text-red-500 transition"
              title="Delete comment"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Rendered markdown content -->
        <div
          class="markdown-body text-sm text-gray-800 dark:text-gray-200"
          v-html="marked.parse(comment.content)"
        />
      </div>
    </div>

    <p v-else class="text-sm text-gray-400 dark:text-gray-600 text-center py-4">
      No comments yet. Be the first to leave a note.
    </p>
  </div>
</template>
