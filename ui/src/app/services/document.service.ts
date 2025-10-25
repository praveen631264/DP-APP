import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpRequest, HttpEvent } from '@angular/common/http';
import { Observable, of } from 'rxjs';

import { Document } from '../models/document.model';

export interface PaginatedDocumentsResponse {
  items: Document[];
  total: number;
}

@Injectable({ providedIn: 'root' })
export class DocumentService {
  // Note: Using a relative URL is best practice for production builds.
  // The proxy.conf.json will handle routing this to the Flask backend during development.
  private apiUrl = '/api/v1';

  constructor(private http: HttpClient) { }

  getDocuments(params: any): Observable<PaginatedDocumentsResponse> {
    let httpParams = new HttpParams();
    // AG-Grid server-side model params
    httpParams = httpParams.set('page', String(params.page));
    httpParams = httpParams.set('limit', String(params.limit));
    if (params.sort_by) {
      httpParams = httpParams.set('sort_by', params.sort_by);
      httpParams = httpParams.set('sort_order', params.sort_order);
    }
    // Add any filters here in the future
    return this.http.get<PaginatedDocumentsResponse>(`${this.apiUrl}/documents`, { params: httpParams });
  }

  getDocumentById(id: string): Observable<Document> {
    return this.http.get<Document>(`${this.apiUrl}/documents/${id}`);
  }

  deleteDocument(id: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/documents/${id}`);
  }

  downloadDocument(id: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/documents/${id}/download`, {
      responseType: 'blob'
    });
  }

  uploadDocument(file: File): Observable<HttpEvent<any>> {
    const formData: FormData = new FormData();
    formData.append('file', file, file.name);

    const req = new HttpRequest('POST', `${this.apiUrl}/documents`, formData, {
      reportProgress: true,
    });

    return this.http.request(req);
  }

  updateKvp(docId: string, kvp: { [key: string]: any }, version: number): Observable<any> {
    const payload = { kvps: kvp, _version: version };
    return this.http.put(`${this.apiUrl}/documents/${docId}/kvp`, payload);
  }
}
