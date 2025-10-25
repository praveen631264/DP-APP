import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// Interface for a single audit log entry from the backend
export interface AuditLog {
  _id: string;
  document_id: string;
  action: string;
  timestamp: string; // ISO date string
  details: any;
  user?: string; // Optional user associated with the action
}

@Injectable({
  providedIn: 'root'
})
export class WorkflowService {
  private apiUrl = '/api/v1/documents';

  constructor(private http: HttpClient) { }

  getDocumentHistory(docId: string): Observable<AuditLog[]> {
    return this.http.get<AuditLog[]>(`${this.apiUrl}/${docId}/history`);
  }

  stopProcessing(docId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/${docId}/stop`, {});
  }

  retryProcessing(docId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/${docId}/reprocess`, {});
  }
}