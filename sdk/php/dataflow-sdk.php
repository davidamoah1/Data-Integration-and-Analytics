<?php
/**
 * DataFlow PHP SDK — Client library for the DataFlow platform.
 *
 * Installation:
 *   composer require dataflow/sdk
 *
 * Usage:
 *   $client = new DataFlowClient(['api_key' => 'dfk_...', 'base_url' => 'http://localhost:8080']);
 *   $dashboards = $client->analytics->listDashboards();
 *   $result = $client->datasets->upload('/path/to/data.csv');
 *   $answer = $client->ai->ask('What are the top trends?');
 */

class DataFlowClient {
    private $apiKey;
    private $baseUrl;

    public $datasets;
    public $analytics;
    public $ai;
    public $workflows;
    public $reports;

    public function __construct($config = []) {
        $this->apiKey = $config['api_key'] ?? getenv('DATAFLOW_API_KEY') ?: '';
        $this->baseUrl = rtrim($config['base_url'] ?? 'http://localhost:8080', '/');
        $this->datasets = new DatasetsAPI($this);
        $this->analytics = new AnalyticsAPI($this);
        $this->ai = new AIAPI($this);
        $this->workflows = new WorkflowsAPI($this);
        $this->reports = new ReportsAPI($this);
    }

    public function get($path) {
        $ch = curl_init($this->baseUrl . $path);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => ["X-API-Key: {$this->apiKey}"],
        ]);
        $resp = curl_exec($ch);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        if ($code >= 400) throw new Exception("API error: $code");
        return json_decode($resp, true);
    }

    public function post($path, $data = null) {
        $ch = curl_init($this->baseUrl . $path);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST => true,
            CURLOPT_HTTPHEADER => ["X-API-Key: {$this->apiKey}", "Content-Type: application/json"],
            CURLOPT_POSTFIELDS => $data ? json_encode($data) : '',
        ]);
        $resp = curl_exec($ch);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        if ($code >= 400) throw new Exception("API error: $code");
        return json_decode($resp, true);
    }

    public function upload($path, $filePath) {
        $ch = curl_init($this->baseUrl . $path);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST => true,
            CURLOPT_HTTPHEADER => ["X-API-Key: {$this->apiKey}"],
            CURLOPT_POSTFIELDS => ['file' => new CURLFile($filePath)],
        ]);
        $resp = curl_exec($ch);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        if ($code >= 400) throw new Exception("API error: $code");
        return json_decode($resp, true);
    }
}

class DatasetsAPI {
    private $client;
    public function __construct($client) { $this->client = $client; }
    public function upload($filePath) { return $this->client->upload('/public/datasets/upload', $filePath); }
    public function list() { return $this->client->get('/public/datasets')['data'] ?? []; }
}

class AnalyticsAPI {
    private $client;
    public function __construct($client) { $this->client = $client; }
    public function listDashboards() { return $this->client->get('/public/analytics/dashboards')['data'] ?? []; }
    public function listKpis() { return $this->client->get('/public/analytics/kpis')['data'] ?? []; }
}

class AIAPI {
    private $client;
    public function __construct($client) { $this->client = $client; }
    public function ask($question) { return $this->client->post('/public/ai/ask', ['question' => $question])['data'] ?? []; }
}

class WorkflowsAPI {
    private $client;
    public function __construct($client) { $this->client = $client; }
    public function list() { return $this->client->get('/public/workflows')['data'] ?? []; }
}

class ReportsAPI {
    private $client;
    public function __construct($client) { $this->client = $client; }
    public function list() { return $this->client->get('/public/reports')['data'] ?? []; }
}
