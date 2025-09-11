#!/usr/bin/env python3
"""
Comprehensive ArXiv MCP Tools Testing Script
"""
import asyncio
import json
import subprocess
import sys
from pathlib import Path

class ArxivMCPTester:
    def __init__(self):
        self.server_path = "/home/lucas_galdino/repositories/mcp_servers/arxiv-mcp-improved"
        self.proc = None
        self.request_id = 1
        
    async def start_server(self):
        """Start the MCP server"""
        self.proc = subprocess.Popen(
            ['uv', 'run', '-m', 'arxiv_mcp'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.server_path
        )
        
        # Initialize the server
        await self._initialize()
        
    async def _initialize(self):
        """Initialize MCP protocol"""
        # Send initialize request
        init_msg = {
            'jsonrpc': '2.0',
            'id': self.request_id,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2025-06-18',
                'capabilities': {'tools': {}},
                'clientInfo': {'name': 'arxiv-test-client', 'version': '1.0.0'}
            }
        }
        self.request_id += 1
        
        await self._send_message(init_msg)
        init_response = await self._read_response()
        
        if 'result' not in init_response:
            raise Exception(f"Initialization failed: {init_response}")
            
        # Send initialized notification
        initialized_msg = {
            'jsonrpc': '2.0',
            'method': 'notifications/initialized',
            'params': {}
        }
        await self._send_message(initialized_msg)
        
        print("✅ MCP Server initialized successfully")
        
    async def _send_message(self, message):
        """Send JSON-RPC message to server"""
        json_msg = json.dumps(message) + '\n'
        self.proc.stdin.write(json_msg)
        self.proc.stdin.flush()
        
    async def _read_response(self):
        """Read JSON-RPC response from server"""
        response_line = self.proc.stdout.readline()
        if not response_line:
            raise Exception("No response from server")
        return json.loads(response_line.strip())
        
    async def call_tool(self, tool_name, arguments):
        """Call a specific MCP tool"""
        request = {
            'jsonrpc': '2.0',
            'id': self.request_id,
            'method': 'tools/call',
            'params': {
                'name': tool_name,
                'arguments': arguments
            }
        }
        self.request_id += 1
        
        await self._send_message(request)
        response = await self._read_response()
        
        if 'error' in response:
            return {'status': 'error', 'error': response['error']['message']}
        elif 'result' in response:
            # Parse the result from MCP format
            result_content = response['result']['content']
            if result_content and len(result_content) > 0:
                # The content is typically in text format, try to parse as JSON
                try:
                    return json.loads(result_content[0]['text'])
                except:
                    return {'status': 'success', 'content': result_content[0]['text']}
        
        return {'status': 'error', 'error': 'Unknown response format'}
        
    async def test_search_arxiv(self):
        """Test the search_arxiv tool"""
        print("\n🔍 Testing: search_arxiv")
        result = await self.call_tool('search_arxiv', {
            'query': 'attention mechanisms neural networks',
            'max_results': 3,
            'category': 'cs.LG'
        })
        
        if result['status'] == 'success':
            print(f"✅ Found {result.get('total_found', 0)} papers")
            return result.get('results', [])
        else:
            print(f"❌ Search failed: {result.get('error')}")
            return []
            
    async def test_fetch_content(self, arxiv_id):
        """Test the fetch_arxiv_paper_content tool"""
        print(f"\n📄 Testing: fetch_arxiv_paper_content (ID: {arxiv_id})")
        result = await self.call_tool('fetch_arxiv_paper_content', {
            'arxiv_id': arxiv_id,
            'include_pdf': False
        })
        
        if result['status'] == 'success':
            content_len = len(result.get('content', ''))
            print(f"✅ Fetched content: {content_len} characters")
            return result.get('content', '')
        else:
            print(f"❌ Fetch failed: {result.get('error')}")
            return ""
            
    async def test_extract_citations(self, text):
        """Test the extract_citations tool"""
        print(f"\n📚 Testing: extract_citations")
        # Use a sample of the text
        sample_text = text[:2000] if len(text) > 2000 else text
        
        result = await self.call_tool('extract_citations', {
            'text': sample_text
        })
        
        if result['status'] == 'success':
            citations_count = result.get('citations_found', 0)
            print(f"✅ Extracted {citations_count} citations")
            return result.get('citations', [])
        else:
            print(f"❌ Citation extraction failed: {result.get('error')}")
            return []
            
    async def test_download_convert(self, arxiv_id):
        """Test the download_and_convert_paper tool"""
        print(f"\n⬇️ Testing: download_and_convert_paper (ID: {arxiv_id})")
        result = await self.call_tool('download_and_convert_paper', {
            'arxiv_id': arxiv_id,
            'output_dir': './test_output',
            'save_latex': True,
            'save_markdown': True,
            'include_pdf': False
        })
        
        if result['status'] == 'success':
            print(f"✅ Download and convert successful")
            return True
        else:
            print(f"❌ Download failed: {result.get('error')}")
            return False
            
    async def test_get_output_structure(self):
        """Test the get_output_structure tool"""
        print(f"\n📁 Testing: get_output_structure")
        result = await self.call_tool('get_output_structure', {
            'output_dir': './test_output'
        })
        
        if result['status'] == 'success':
            print(f"✅ Output structure retrieved")
        else:
            print(f"❌ Output structure failed: {result.get('error')}")
            
    async def test_processing_metrics(self):
        """Test the get_processing_metrics tool"""
        print(f"\n📊 Testing: get_processing_metrics")
        result = await self.call_tool('get_processing_metrics', {
            'time_range': '24h'
        })
        
        if result['status'] == 'success':
            print(f"✅ Processing metrics retrieved")
        else:
            print(f"❌ Metrics failed: {result.get('error')}")
            
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        try:
            await self.start_server()
            
            print("🚀 Starting ArXiv MCP Tools Test Suite")
            print("=" * 50)
            
            # 1. Search for papers
            papers = await self.test_search_arxiv()
            
            if papers:
                # Get the first paper ID for further testing
                first_paper = papers[0]
                arxiv_id = first_paper.get('id', '').replace('http://arxiv.org/abs/', '')
                
                if arxiv_id:
                    # 2. Fetch content
                    content = await self.test_fetch_content(arxiv_id)
                    
                    # 3. Extract citations
                    if content:
                        citations = await self.test_extract_citations(content)
                    
                    # 4. Download and convert
                    success = await self.test_download_convert(arxiv_id)
                    
                    # 5. Check output structure
                    if success:
                        await self.test_get_output_structure()
            
            # 6. Get processing metrics
            await self.test_processing_metrics()
            
            print("\n" + "=" * 50)
            print("🎉 Test Suite Completed!")
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.proc:
                self.proc.terminate()
                self.proc.wait()

async def main():
    tester = ArxivMCPTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
