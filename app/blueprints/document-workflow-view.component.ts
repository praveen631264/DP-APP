import { Component, computed, effect, input, signal } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { HttpErrorResponse } from '@angular/common/http';
import { of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Document } from '../../services/document.service';
import { AuditLog, WorkflowService } from '../../services/workflow.service';
import { Edge, Node } from '@swimlane/ngx-graph';

@Component({
  selector: 'app-document-workflow-view',
  templateUrl: './document-workflow-view.component.html',
  styleUrls: ['./document-workflow-view.component.scss']
})
export class DocumentWorkflowViewComponent {
  document = input.required<Document>();

  // ngx-graph properties
  nodes: Node[] = [];
  links: Edge[] = [];
  
  history = signal<AuditLog[]>([]); // Keep history for the log panel
  isLoading = signal(false);
  isActionLoading = signal(false);

  // Button disabled states
  canRetry = computed(() => {
    const status = this.document().status;
    const retryableStatuses = ['Failed', 'Error', 'Force Stopped', 'Playbook Failed', 'Orchestration Failed', 'INTERRUPTED'];
    return retryableStatuses.includes(status);
  });
  canStop = computed(() => {
    const status = this.document().status;
    const stoppableStatuses = ['Processing', 'Queued for Orchestration', 'Queued for Reprocessing', 'Chunks Processed', 'INTERRUPTED'];
    return stoppableStatuses.includes(status);
  });

  constructor(
    private workflowService: WorkflowService,
    private snackBar: MatSnackBar,
  ) {
    effect(() => {
      // This effect will re-run whenever the document input changes.
      this.fetchHistory();
    });
  }

  private buildGraphFromHistory(history: AuditLog[]): void {
    if (!history || history.length === 0) {
      this.nodes = [];
      this.links = [];
      return;
    }

    const uniqueActions = [...new Map(history.map(item => [item.action, item])).values()]
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

    const newNodes: Node[] = uniqueActions.map((event, index) => {
      const isFailed = event.action.toLowerCase().includes('fail');
      const isStopped = event.action.toLowerCase().includes('stop');
      const isCurrent = index === uniqueActions.length - 1;

      let color = '#28a745'; // Green for success
      if (isFailed) color = '#dc3545'; // Red for fail
      if (isStopped) color = '#ffc107'; // Yellow for stop
      if (isCurrent && !isFailed && !isStopped) color = '#007bff'; // Blue for current

      return {
        id: `node${index}`,
        label: event.action,
        data: {
          color: color,
          isCurrent: isCurrent
        }
      };
    });

    const newLinks: Edge[] = [];
    for (let i = 0; i < newNodes.length - 1; i++) {
      newLinks.push({
        id: `link${i}`,
        source: `node${i}`,
        target: `node${i + 1}`
      });
    }

    this.nodes = newNodes;
    this.links = newLinks;
  }

  fetchHistory(): void {
    const doc = this.document();
    if (!doc) return;
    this.isLoading.set(true);
    this.workflowService.getDocumentHistory(doc._id).pipe(
      catchError((err: HttpErrorResponse) => {
        this.snackBar.open(`Error fetching history: ${err.error?.error || err.message}`, 'Close', { duration: 5000 });
        return of([]);
      })
    ).subscribe(history => {
      const sortedHistory = [...history].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()); // Show latest first in log
      this.history.set(sortedHistory);
      this.buildGraphFromHistory(history);
      this.isLoading.set(false);
    });
  }

  onStop(): void {
    if (!this.canStop()) return;
    this.isActionLoading.set(true);
    this.workflowService.stopProcessing(this.document()._id).subscribe({
      next: (res) => {
        this.snackBar.open(res.message || 'Stop signal sent successfully.', 'Close', { duration: 3000 });
        this.isActionLoading.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.snackBar.open(`Error: ${err.error?.error || 'Could not stop processing.'}`, 'Close', { duration: 5000 });
        this.isActionLoading.set(false);
      }
    });
  }

  onRetry(): void {
    if (!this.canRetry()) return;
    this.isActionLoading.set(true);
    this.workflowService.retryProcessing(this.document()._id).subscribe({
      next: (res) => {
        this.snackBar.open(res.message || 'Reprocessing has been queued.', 'Close', { duration: 3000 });
        this.isActionLoading.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.snackBar.open(`Error: ${err.error?.error || 'Could not retry processing.'}`, 'Close', { duration: 5000 });
        this.isActionLoading.set(false);
      }
    });
  }
}