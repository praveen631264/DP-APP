import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { mockDocuments } from './mock-data';

export interface Document {
  id: string;
  name: string;
  categoryId: string;
  kvp_extraction: any;
  kvData?: { key: string; value: string }[];
}

@Injectable({
  providedIn: 'root'
})
export class DocumentService {

  private apiUrl = 'http://localhost:8080/api/documents';
  private useMockData = true;

  constructor(private http: HttpClient) { }

  getDocuments(categoryId?: string): Observable<Document[]> {
    if (this.useMockData) {
      console.log('Using mock documents');
      let documents = mockDocuments;
      if (categoryId) {
        documents = documents.filter(doc => doc.categoryId === categoryId);
      }
      return of(documents as any);
    }

    let url = this.apiUrl;
    if (categoryId) {
      url += `?categoryId=${categoryId}`;
    }
    return this.http.get<Document[]>(url).pipe(
      tap(documents => console.log('Fetched documents:', documents)),
      catchError(error => {
        console.error('Error fetching documents:', error);
        return of([]);
      })
    );
  }

  uploadFile(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/upload`, formData, {
      reportProgress: true,
      observe: 'events'
    });
  }

  uploadDocument(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/upload`, formData, {
      reportProgress: true,
      observe: 'events'
    });
  }

  updateKVP(docId: string, kvp: { [key: string]: string }): Observable<Document> {
    return this.http.put<Document>(`${this.apiUrl}/${docId}/kvp`, kvp);
  }

  addKVP(docId: string, key: string, value: string): Observable<{ document: Document }> {
    return this.http.post<{ document: Document }>(`${this.apiUrl}/${docId}/kvp`, { key, value });
  }

  deleteKVP(docId: string, key: string): Observable<{ document: Document }> {
    return this.http.delete<{ document: Document }>(`${this.apiUrl}/${docId}/kvp/${key}`);
  }

  recategorizeDocument(docId: string, newCategoryId: string, explanation: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/${docId}/recategorize`, { new_category_id: newCategoryId, explanation });
  }

  categorizeDocument(docId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/${docId}/categorize`, {});
  }

  extractKvPairs(docId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/${docId}/extract-kv-pairs`, {});
  }

  setUseMock(useMock: boolean): void {
    this.useMockData = useMock;
    window.location.reload();
  }
}
