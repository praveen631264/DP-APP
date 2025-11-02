
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
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
  private headers = new HttpHeaders({ 'X-Proxy-To': 'flask-app' });

  constructor(private http: HttpClient) { }

  getDocuments(params: any): Observable<PaginatedDocumentsResponse> {
    return this.http.get<PaginatedDocumentsResponse>(this.apiUrl, { params, headers: this.headers });
  }

  getDocument(docId: string): Observable<Document> {
    return this.http.get<Document>(`${this.apiUrl}/${docId}`, { headers: this.headers });
  }

  uploadDocument(formData: FormData): Observable<any> {
    return this.http.post(this.apiUrl, formData, {
      reportProgress: true,
      observe: 'events',
      headers: this.headers
    });
  }

  deleteDocument(docId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${docId}`, { headers: this.headers });
  }

  updateDocumentKvps(docId: string, kvps: { [key: string]: any }, version: number): Observable<any> {
    return this.http.put(`${this.apiUrl}/${docId}/kvp`, { kvps, _version: version }, { headers: this.headers });
  }
}
