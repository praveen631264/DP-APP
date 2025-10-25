import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { SocketIOService } from './socket-io.service';

export interface DocumentStatusUpdate {
  doc_id: string;
  status: string;
}

@Injectable({
  providedIn: 'root'
})
export class SocketService {

  constructor(private socketIoService: SocketIOService) { }

  onDocumentStatusChanged(): Observable<DocumentStatusUpdate> {
    return this.socketIoService.on('document_status_changed');
  }
}