import textract
import re
from enum import Enum
from collections import deque

class Type(Enum):
    TITLE = 1
    HEADER = 2
    ITALIC = 3
    LIST = 4
    TEXT = 5

class Document:
    def __init__(self, text):
        self.sections = []
        tokens = text.splitlines()
        """空行をスキップする"""
        tokens = list(filter(lambda s: s != '', tokens))
        self.tokens = tokens
    
    def read(self):
        sections = []
        q = deque(self.tokens)

        title = TitleSection(q)
        title.read()
        sections.append(title)

        toc = TOCSection(q)
        toc.read()
        sections.append(toc)

        # ページ番号を除去する
        page_num = 1
        def get_and_inc_page_num():
            nonlocal page_num
            pre_page_num = page_num
            page_num += 1
            return pre_page_num
        q = deque(filter(lambda s: not (s.isdecimal() and int(s) == get_and_inc_page_num()), q))

        while q:
            normal = NormalSection(q)
            normal.read()
            sections.append(normal)
        
        return '\n'.join(map(str, sections))

class Section:
    def __init__(self, tokens):
        self.elements = []
        self.tokens = tokens
    
    def __str__(self):
        return '\n'.join(map(str, self.elements))
    
    def read(self):
        pass

    def next_token(self, predicate=lambda _: True):
        return self.tokens.popleft() if predicate(self.tokens[0]) else None

class TitleSection(Section):
    def __init__(self, tokens):
        super().__init__(tokens)
    
    def read(self):
        self.elements.append(Element(self.next_token(), Type.TITLE))
        self.elements.append(Element(self.next_token(), Type.HEADER))
        self.elements.append(Element(self.next_token(), Type.ITALIC))

class TOCSection(Section):
    def __init__(self, tokens):
        super().__init__(tokens)
    
    def read(self):
        self.elements.append(Element(self.next_token(), Type.HEADER))
        self.elements.extend(self.read_contents())
    
    """目次の1行分を取得する"""
    def read_item(self):
        line = ' '.join([self.next_token() for _ in range(3)])
        return Element(line, Type.LIST)
    
    """目次の終わりまでを列挙する"""
    def read_contents(self):
        while not self.tokens[0].isdecimal():
            yield self.read_item()

class NormalSection(Section):
    def __init__(self, tokens):
        super().__init__(tokens)
    
    def read(self):
        self.elements.append(Element(self.next_token(), Type.HEADER))
        self.elements.append(Element(self.next_token(), Type.HEADER))
        self.elements.extend(self.read_chapter())

    """文章を取得する"""
    def read_sentence(self):
        sentence = ''
        while s := self.next_token(lambda s: not re.match(r'[.!:]', s[-1])):
            sentence += s + ' '
        sentence += self.next_token()
        if sentence[0] == '•':
            return Element(sentence[2:], Type.LIST)
        else :
            return Element(sentence, Type.TEXT)
    
    """チャプターの終わりまでを列挙する"""
    def read_chapter(self):
        while self.tokens and not re.match(r'Chapter [IVX]+', self.tokens[0]):
            yield self.read_sentence()

class Element:
    def __init__(self, text, type):
        self.text = text
        self.type = type
    
    def __str__(self):
        if self.type == Type.TITLE:
            return '# ' + self.text
        elif self.type == Type.HEADER:
            return '## ' + self.text
        elif self.type == Type.ITALIC:
            return '*' + self.text + '*'
        elif self.type == Type.LIST:
            return '- ' + self.text
        elif self.type == Type.TEXT:
            return self.text + '  '

def main():
    text = textract.process('en.subject.pdf').decode('utf-8')
    doc = Document(text)
    print(doc.read())

if __name__ == "__main__":
    main()
