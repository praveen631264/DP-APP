import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ChatMessage {
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {

  private apiUrl = '/api/chat';

  constructor(private http: HttpClient) { }

  sendGlobalMessage(message: string, sid: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/global`, { message, sid });
  }

  sendDocumentMessage(message: string, documentId: string): Observable<ChatMessage> {
    return this.http.post<ChatMessage>(`${this.apiUrl}/document`, { message, document_id: documentId });
  }
}
