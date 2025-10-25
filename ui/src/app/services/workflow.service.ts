import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map } from 'rxjs/operators';

// Define interfaces for the data structures
export interface AuditLog {
  doc_id: string;
  action: string;
  timestamp: string;
  details: any;
}

export interface Workflow {
  nodes: { id: string; label: string; data: { color: string } }[];
  links: { source: string; target: string }[];
  currentStageId: string;
}

export interface StageDetails {
  processes: { id: string; name: string; status: string; logs: string }[];
  logs: string;
}

@Injectable({
  providedIn: 'root'
})
export class WorkflowService {

  private apiUrl = '/api/documents';

  constructor(private http: HttpClient) { }

  getWorkflow(documentId: string): Observable<Workflow> {
    return this.http.get<AuditLog[]>(`${this.apiUrl}/${documentId}/history`).pipe(
      map(history => {
        const nodes = history.map((log, index) => ({
          id: (index + 1).toString(),
          label: log.action,
          data: { color: '#28a745' } // Default color, can be changed based on status
        }));

        const links = [];
        for (let i = 0; i < nodes.length - 1; i++) {
          links.push({ source: nodes[i].id, target: nodes[i + 1].id });
        }

        const currentStageId = nodes.length > 0 ? nodes[nodes.length - 1].id : '1';

        return { nodes, links, currentStageId };
      })
    );
  }

  getStageDetails(stageId: string, documentId: string): Observable<any> {
    // The stageId is the index of the node in the graph.
    // We need to get the history and find the details for that stage.
    return this.http.get<AuditLog[]>(`${this.apiUrl}/${documentId}/history`).pipe(
      map(history => {
        const stageIndex = parseInt(stageId, 10) - 1;
        if (history && history[stageIndex]) {
          return history[stageIndex].details;
        }
        return null;
      })
    );
  }

  retryProcess(documentId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/${documentId}/reprocess`, {});
  }

  stopProcess(documentId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/${documentId}/stop`, {});
  }

  pauseProcess(processId: string): Observable<any> {
    console.log(`Pausing process: ${processId}`);
    // No backend endpoint for this yet.
    return of({ success: true });
  }
}