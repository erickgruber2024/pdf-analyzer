import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, catchError, throwError } from 'rxjs'; // Import catchError and throwError for better error handling

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  // Base URL for your Flask backend API
  private apiUrl = 'http://localhost:5000/api/v1'; // Ensure this matches your backend host/port

  constructor(private http: HttpClient) {}

  /**
   * Tests the connection to the backend.
   * @returns Observable with the backend response.
   */
  testConnection(): Observable<any> { // Consider defining an interface for the response shape
    return this.http.get<any>(`${this.apiUrl}/test_connection`)
      .pipe(catchError(this.handleError)); // Add error handling
  }

  /**
   * Uploads a PDF file using FormData.
   * @param formData The FormData object containing the file.
   * @returns Observable with the backend response (including pdf_id).
   */
  uploadPdf(formData: FormData): Observable<any> { // Consider defining an interface for the response shape
    return this.http.post<any>(`${this.apiUrl}/upload_pdf`, formData)
      .pipe(catchError(this.handleError)); // Add error handling
  }

  /**
   * Sends a request to the backend to start the analysis process for a given PDF ID.
   * @param pdfId The ID of the PDF to analyze.
   * @returns Observable with the backend response.
   */
  analyzePdf(pdfId: number): Observable<any> { // Consider defining an interface for the response shape
    // POST request, as the backend endpoint is defined with POST
    // The body can be empty if the backend doesn't require anything, or send {}
    return this.http.post<any>(`${this.apiUrl}/analyze_pdf/${pdfId}`, {})
      .pipe(catchError(this.handleError)); // Add error handling
  }

  /**
   * Fetches the analysis results (extracted components) for a given PDF ID.
   * This replaces the old 'getData' method.
   * @param pdfId The ID of the PDF whose results are needed.
   * @returns Observable containing the analysis results.
   */
  getAnalysisResults(pdfId: number): Observable<any> { // Consider defining an interface for the response shape { pdf_id: number, analysis_type: string, components: string[] }
    return this.http.get<any>(`${this.apiUrl}/analysis_results/${pdfId}`)
      .pipe(catchError(this.handleError)); // Add error handling
  }

  /**
   * Basic centralized error handler for HTTP requests.
   * Logs the error and returns an Observable that emits the error.
   * @param error The HttpErrorResponse object.
   * @returns An Observable that throws the processed error.
   */
  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An unknown error occurred!';
    if (error.error instanceof ErrorEvent) {
      // Client-side or network error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Backend returned an unsuccessful response code.
      // The response body may contain clues as to what went wrong.
      // Try to get the error message from the backend response body
      errorMessage = `Server returned code ${error.status}, error message is: ${error.error?.error || error.message}`;
    }
    console.error(error); // Log the full error object to the console
    return throwError(() => new Error(errorMessage)); // Return an observable throwing an error
  }
}