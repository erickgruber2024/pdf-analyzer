import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private apiUrl = 'http://localhost:5000/api/v1';

  constructor(private http: HttpClient) {}

  testConnection() {
    return this.http.get(`${this.apiUrl}/test_connection`);
  }

  uploadPdf(formData: FormData) {
    return this.http.post(`${this.apiUrl}/upload_pdf`, formData);
  }

  getData() {
    return this.http.get(`${this.apiUrl}/get_data`);
  }
}
