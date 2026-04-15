import { Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';

const { Text } = Typography;

interface Props {
  table: any[][];
  title?: string;
  maxHeight?: number;
}

export default function TablePreview({ table, title, maxHeight = 400 }: Props) {
  if (!table || table.length === 0) return null;

  const headers = table[0];
  const dataRows = table.slice(1);

  const columns: ColumnsType<Record<string, any>> = headers.map((h: any, i: number) => ({
    title: String(h ?? `Col ${i}`),
    dataIndex: `col_${i}`,
    key: `col_${i}`,
    ellipsis: true,
    width: 140,
    render: (val: any) => {
      if (val === null || val === undefined || val === '') {
        return <Text type="secondary" italic>—</Text>;
      }
      if (typeof val === 'number') {
        return <Tag color="blue">{val}</Tag>;
      }
      return <Text>{String(val)}</Text>;
    },
  }));

  const dataSource = dataRows.map((row, rowIdx) => {
    const record: Record<string, any> = { key: rowIdx };
    row.forEach((cell: any, colIdx: number) => {
      record[`col_${colIdx}`] = cell;
    });
    return record;
  });

  return (
    <div>
      {title && (
        <Text strong style={{ display: 'block', marginBottom: 8 }}>
          {title}
        </Text>
      )}
      <Table
        columns={columns}
        dataSource={dataSource}
        size="small"
        bordered
        pagination={dataRows.length > 20 ? { pageSize: 20, size: 'small' } : false}
        scroll={{ x: 'max-content', y: maxHeight }}
        style={{ fontSize: 13 }}
      />
    </div>
  );
}
