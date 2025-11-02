
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Document } from '../models/document.model';
import { environment } from '../../environments/environment';

export interface PaginatedDocumentsResponse {
  items: Document[];
  total: number;
}

@Injectable({
  providedIn: 'root'
})
export class DocumentService {
  private apiUrl = `${environment.apiUrl}/documents`;

  constructor(private http: HttpClient) { }

  getDocuments(params: any): Observable<PaginatedDocumentsResponse> {
    return this.http.get<PaginatedDocumentsResponse>(this.apiUrl, { params });
  }

  getDocument(docId: string): Observable<Document> {
    return this.http.get<Document>(`${this.apiUrl}/${docId}`);
  }

  uploadDocument(formData: FormData): Observable<any> {
    return this.http.post(this.apiUrl, formData, {
      reportProgress: true,
      observe: 'events'
    });
  }

  deleteDocument(docId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${docId}`);
  }

  updateDocumentKvps(docId: string, kvps: { [key: string]: any }, version: number): Observable<any> {
    return this.http.put(`${this.apiUrl}/${docId}/kvp`, { kvps, _version: version });
  }
}
