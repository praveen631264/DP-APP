import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { SocketIoService } from './socket-io.service';

@Injectable({
  providedIn: 'root'
})
export class GlobalChatService {
  private apiUrl = '/api/v1/chat/global';

  constructor(private http: HttpClient, private socketService: SocketIoService) {}

  sendMessage(message: string): void {
    const sid = this.socketService.getSessionId();
    if (!sid) {
      console.error("Socket.IO session ID not available.");
      return;
    }
    const payload = { message, sid };
    this.http.post(this.apiUrl, payload).subscribe(); // Fire and forget
  }

  getChatStream(): Observable<{ token?: string }> {
    return this.socketService.listen<{ token?: string }>('chat_token');
  }

  getChatEndStream(): Observable<{}> {
    return this.socketService.listen<{}>('chat_end');
  }
}